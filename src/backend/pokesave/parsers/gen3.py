"""Gen III save file parser (Ruby/Sapphire/Emerald/FireRed/LeafGreen).

Gen 3 saves are 128 KiB (0x20000 bytes) with two save blocks of 14 sections
each. Each section is 4096 bytes with a footer containing section ID, checksum,
and save index. Sections are physically shuffled (rotated) on each save.

Pokemon data uses XOR encryption with PID^OTID and 24 substructure permutations.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_III)
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_substructures_(Generation_III)
"""

from __future__ import annotations

import logging
import struct

from pokesave.crypto.gen3 import (
    decrypt_pokemon_data,
    get_substructure_order,
    pokemon_checksum,
    section_checksum,
)
from pokesave.data.natures import NATURE_NAMES
from pokesave.data.species import SPECIES_NAMES, gen3_species_to_national
from pokesave.encoding.gen3 import decode_string
from pokesave.models import (
    EVs,
    Item,
    IVs,
    Move,
    Playtime,
    Pokemon,
    SaveFile,
    Stats,
    Trainer,
)
from pokesave.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SECTOR_SIZE = 0x1000  # 4096 bytes per sector
_NUM_SECTORS = 14
_BLOCK_SIZE = _SECTOR_SIZE * _NUM_SECTORS  # 0xE000

_DATA_SIZE = 3968  # usable data payload per section (0x000-0xF7F)

# Footer offsets within a sector (relative to sector start)
_FOOTER_SECTION_ID = 0xFF4
_FOOTER_CHECKSUM = 0xFF6
_FOOTER_SAVE_INDEX = 0xFF8

# Pokemon data sizes
_BOX_POKEMON_SIZE = 80
_PARTY_POKEMON_SIZE = 100
_ENCRYPTED_SIZE = 48
_HEADER_SIZE = 32
_SUBSTRUCTURE_SIZE = 12

# PC box constants
_NUM_BOXES = 14
_POKEMON_PER_BOX = 30

# Ball names (Gen 3 ball index -> name)
_BALL_NAMES: dict[int, str] = {
    1: "Master Ball",
    2: "Ultra Ball",
    3: "Great Ball",
    4: "Poke Ball",
    5: "Safari Ball",
    6: "Net Ball",
    7: "Dive Ball",
    8: "Nest Ball",
    9: "Repeat Ball",
    10: "Timer Ball",
    11: "Luxury Ball",
    12: "Premier Ball",
}

# Game origin codes from origins info
_GAME_ORIGIN: dict[int, str] = {
    1: "Sapphire",
    2: "Ruby",
    3: "Emerald",
    4: "FireRed",
    5: "LeafGreen",
    15: "Colosseum/XD",
}

# Section data sizes (how many bytes of payload to checksum per section ID)
_SECTION_SIZES: dict[int, int] = {
    0: 3884,
    1: 3968,
    2: 3968,
    3: 3968,
    4: 3848,
    5: 3968,
    6: 3968,
    7: 3968,
    8: 3968,
    9: 3968,
    10: 3968,
    11: 3968,
    12: 3968,
    13: 2000,
}


def _safe_species_name(species_id: int) -> str:
    """Look up species name, returning a fallback string for unknown IDs."""
    return SPECIES_NAMES.get(species_id, f"Pokemon #{species_id}")


def _safe_move_name(move_id: int) -> str:
    """Look up move name with fallback."""
    try:
        from pokesave.data.moves import MOVE_NAMES
        return MOVE_NAMES.get(move_id, f"Move #{move_id}")
    except ImportError:
        return f"Move #{move_id}"


def _safe_item_name(item_id: int) -> str:
    """Look up item name with fallback."""
    try:
        from pokesave.data.items import GEN3_ITEMS
        return GEN3_ITEMS.get(item_id, f"Item #{item_id}")
    except ImportError:
        return f"Item #{item_id}"


def _safe_location_name(loc_id: int) -> str:
    """Look up location name with fallback."""
    try:
        from pokesave.data.locations import GEN3_LOCATIONS
        return GEN3_LOCATIONS.get(loc_id, f"Location #{loc_id}")
    except ImportError:
        return f"Location #{loc_id}"


def _safe_nature_name(nature_id: int) -> str:
    """Look up nature name with fallback."""
    return NATURE_NAMES.get(nature_id, f"Nature #{nature_id}")


class Gen3Parser(BaseParser):
    """Parser for Generation III Pokemon save files."""

    def parse(self, data: bytes) -> SaveFile:
        """Parse a Gen 3 save file into a structured SaveFile model."""
        # Trim emulator footers (RTC, DeSmuME, etc.) to reach a known size
        if len(data) not in (0x20000, 0x10000):
            from pokesave.detect import _trim_emulator_footer
            data = _trim_emulator_footer(data)
        if len(data) not in (0x20000, 0x10000):
            raise ValueError(
                f"Gen 3 save file must be 131072 (128 KiB) or 65536 (64 KiB) bytes, got {len(data)}"
            )

        game = self.detect_version(data)

        # Determine active save block
        active_offset = self._get_active_block_offset(data)

        # Build section map: section_id -> physical_offset
        section_map = self._build_section_map(data, active_offset)

        # Parse trainer info from section 0
        trainer = self._parse_trainer(data, section_map, game)

        # Parse party Pokemon from section 1
        party = self._parse_party(data, section_map, game)

        # Parse PC boxes from sections 5-13
        boxes = self._parse_pc_boxes(data, section_map, game)

        # Bag parsing (simplified -- section 1-2 depending on game)
        bag = self._parse_bag(data, section_map, game)

        return SaveFile(
            generation=3,
            game=game,
            trainer=trainer,
            party=party,
            boxes=boxes,
            bag=bag,
        )

    def validate_checksum(self, data: bytes) -> bool:
        """Validate checksums for all 14 sections in both save blocks."""
        block_offsets = [0x0000]
        if len(data) >= _BLOCK_SIZE * 2:
            block_offsets.append(_BLOCK_SIZE)
        for block_offset in block_offsets:
            for i in range(_NUM_SECTORS):
                sector_start = block_offset + i * _SECTOR_SIZE

                # Read section ID and stored checksum from footer
                section_id = struct.unpack_from(
                    "<H", data, sector_start + _FOOTER_SECTION_ID
                )[0]
                stored_checksum = struct.unpack_from(
                    "<H", data, sector_start + _FOOTER_CHECKSUM
                )[0]

                if section_id > 13:
                    continue

                # Compute checksum over the relevant data payload
                payload_size = _SECTION_SIZES.get(section_id, _DATA_SIZE)
                payload = data[sector_start : sector_start + payload_size]
                computed = section_checksum(payload)

                if computed != stored_checksum:
                    logger.warning(
                        "Section %d at offset 0x%X: checksum mismatch "
                        "(stored=0x%04X, computed=0x%04X)",
                        section_id,
                        sector_start,
                        stored_checksum,
                        computed,
                    )
                    return False

        return True

    def detect_version(self, data: bytes) -> str:
        """Detect the specific Gen 3 game version.

        Uses the uint32 at Section 0 offset 0xAC and the Emerald data range.
        """
        # Find section 0 in the active block
        active_offset = self._get_active_block_offset(data)
        section_map = self._build_section_map(data, active_offset)

        if 0 not in section_map:
            return "Unknown Gen 3"

        section0_offset = section_map[0]
        version_offset = section0_offset + 0xAC

        if version_offset + 4 > len(data):
            return "Unknown Gen 3"

        version_val = struct.unpack_from("<I", data, version_offset)[0]

        if version_val == 1:
            return "FireRed/LeafGreen"
        if version_val == 0:
            # Check Emerald-specific range for non-zero data
            start = section0_offset + 0x890
            end = min(section0_offset + 0xF2C, section0_offset + _DATA_SIZE)
            if any(data[i] != 0 for i in range(start, min(end, len(data)))):
                return "Emerald"
            return "Ruby/Sapphire"

        # Non-zero, non-one: likely Emerald
        start = section0_offset + 0x890
        end = min(section0_offset + 0xF2C, section0_offset + _DATA_SIZE)
        if any(data[i] != 0 for i in range(start, min(end, len(data)))):
            return "Emerald"
        return "Ruby/Sapphire"

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _get_active_block_offset(self, data: bytes) -> int:
        """Determine which of the two save blocks is active (higher save index).

        Half-size saves (64 KiB) only have block A at offset 0x0000.
        """
        if len(data) < _BLOCK_SIZE * 2:
            # Half-size save: only one block
            return 0x0000

        save_idx_a = struct.unpack_from(
            "<I", data, 0x0000 + _FOOTER_SAVE_INDEX
        )[0]
        save_idx_b = struct.unpack_from(
            "<I", data, _BLOCK_SIZE + _FOOTER_SAVE_INDEX
        )[0]

        if save_idx_b > save_idx_a:
            return _BLOCK_SIZE
        return 0x0000

    def _build_section_map(
        self, data: bytes, block_offset: int
    ) -> dict[int, int]:
        """Build a mapping of section_id -> physical offset within a save block."""
        section_map: dict[int, int] = {}
        for i in range(_NUM_SECTORS):
            sector_start = block_offset + i * _SECTOR_SIZE
            section_id = struct.unpack_from(
                "<H", data, sector_start + _FOOTER_SECTION_ID
            )[0]
            if section_id <= 13:
                section_map[section_id] = sector_start
        return section_map

    def _parse_trainer(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> Trainer:
        """Parse trainer info from Section 0."""
        if 0 not in section_map:
            raise ValueError("Section 0 (Trainer Info) not found in save data")

        base = section_map[0]

        # Player name: 7 bytes + terminator at 0x000
        name = decode_string(data[base : base + 8])

        # Gender: 0x008
        gender_byte = data[base + 0x008]
        gender = "Female" if gender_byte == 1 else "Male"

        # TID/SID: 0x00A (u32 LE, lower 16=TID, upper 16=SID)
        tid_sid = struct.unpack_from("<I", data, base + 0x00A)[0]
        tid = tid_sid & 0xFFFF
        sid = (tid_sid >> 16) & 0xFFFF

        # Playtime: hours at 0x00E (u16), minutes at 0x010, seconds at 0x011
        hours = struct.unpack_from("<H", data, base + 0x00E)[0]
        minutes = data[base + 0x010]
        seconds = data[base + 0x011]

        # Money: varies by game version. In Emerald and FRLG, the stored
        # value is XOR-encrypted with a Security Key.
        # RS: Section 1 offset 0x0490 (no encryption)
        # Emerald: Section 1 offset 0x0490 (encrypted)
        # FRLG: Section 1 offset 0x0290 (encrypted)
        money = 0
        security_key = self._get_security_key(data, section_map, game)
        if 1 in section_map:
            sec1 = section_map[1]
            if "FireRed" in game or "LeafGreen" in game:
                money_offset = sec1 + 0x0290
            else:
                money_offset = sec1 + 0x0490
            if money_offset + 4 <= len(data):
                raw_money = struct.unpack_from("<I", data, money_offset)[0]
                money = (raw_money ^ security_key) & 0xFFFFFFFF

        # Badges: stored as a bitmask in Section 0
        # RS/E: offset 0x27 in trainer info area
        # FRLG: different offset
        badges = self._parse_badges(data, section_map, game)

        # Pokedex: Section 0 contains owned/seen bitfields
        pokedex_owned, pokedex_seen = self._parse_pokedex(data, section_map, game)

        return Trainer(
            name=name,
            id=tid,
            secret_id=sid,
            gender=gender,
            money=money,
            badges=badges,
            playtime=Playtime(hours=hours, minutes=minutes, seconds=seconds),
            pokedex_owned=pokedex_owned,
            pokedex_seen=pokedex_seen,
        )

    def _parse_badges(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> list[str]:
        """Parse badge bitmask from save data."""
        if 0 not in section_map:
            return []

        base = section_map[0]

        if "FireRed" in game or "LeafGreen" in game:
            badge_names = [
                "Boulder", "Cascade", "Thunder", "Rainbow",
                "Soul", "Marsh", "Volcano", "Earth",
            ]
        elif "Emerald" in game or "Ruby" in game or "Sapphire" in game:
            badge_names = [
                "Stone", "Knuckle", "Dynamo", "Heat",
                "Balance", "Feather", "Mind", "Rain",
            ]
        else:
            badge_names = [
                "Badge 1", "Badge 2", "Badge 3", "Badge 4",
                "Badge 5", "Badge 6", "Badge 7", "Badge 8",
            ]

        # Badge flags are in the trainer flags section
        # The exact offset varies but typically section 2 contains flags
        # For a best-effort approach, look at a known offset
        # RS: Section 0 at offset 0x0F, FRLG differs
        # This is approximate -- exact offsets need to be game-specific
        if 2 in section_map:
            flags_base = section_map[2]
            # Badges are typically stored early in the flags section
            badge_byte = data[flags_base] if flags_base < len(data) else 0
        else:
            badge_byte = 0

        badges = []
        for i, name in enumerate(badge_names):
            if badge_byte & (1 << i):
                badges.append(name)

        return badges

    def _parse_pokedex(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> tuple[int, int]:
        """Parse Pokedex owned/seen counts from Section 0."""
        if 0 not in section_map:
            return (0, 0)

        base = section_map[0]

        # Pokedex owned bitfield: offset 0x28 (49 bytes = 386 bits + padding)
        # Pokedex seen bitfield: offset 0x5C
        # These offsets vary slightly by game version
        if "FireRed" in game or "LeafGreen" in game:
            owned_offset = base + 0x28
            seen_offset = base + 0x5C
        else:
            owned_offset = base + 0x28
            seen_offset = base + 0x5C

        owned = self._count_bits(data, owned_offset, 49)
        seen = self._count_bits(data, seen_offset, 49)

        return (owned, seen)

    def _count_bits(self, data: bytes, offset: int, num_bytes: int) -> int:
        """Count the number of set bits in a range of bytes."""
        count = 0
        end = min(offset + num_bytes, len(data))
        for i in range(offset, end):
            count += bin(data[i]).count("1")
        return count

    def _get_security_key(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> int:
        """Get the Security Key used to XOR-encrypt money and bag quantities.

        Ruby/Sapphire: no encryption (key = 0).
        Emerald: key is at Section 0, offset 0xAC (4 bytes).
        FireRed/LeafGreen: key is at Section 0, offset 0xAF8 (4 bytes).
        """
        if "Ruby" in game or "Sapphire" in game:
            return 0

        if 0 not in section_map:
            return 0

        base = section_map[0]

        if "Emerald" in game:
            key_offset = base + 0xAC
        elif "FireRed" in game or "LeafGreen" in game:
            key_offset = base + 0xAF8
        else:
            return 0

        if key_offset + 4 > len(data):
            return 0

        return struct.unpack_from("<I", data, key_offset)[0]

    def _parse_party(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> list[Pokemon]:
        """Parse party Pokemon from Section 1."""
        if 1 not in section_map:
            return []

        base = section_map[1]

        # Party data location varies by game
        if "FireRed" in game or "LeafGreen" in game:
            party_offset = base + 0x0034
        else:
            # RS/Emerald
            party_offset = base + 0x0234

        if party_offset + 4 > len(data):
            return []

        party_count = struct.unpack_from("<I", data, party_offset)[0]
        if party_count > 6:
            party_count = 6

        pokemon_start = party_offset + 4
        party = []

        for i in range(party_count):
            offset = pokemon_start + i * _PARTY_POKEMON_SIZE
            if offset + _PARTY_POKEMON_SIZE > len(data):
                break

            pkmn_data = data[offset : offset + _PARTY_POKEMON_SIZE]
            try:
                pkmn = self._parse_pokemon(pkmn_data, is_party=True, location="party")
                if pkmn is not None:
                    party.append(pkmn)
            except Exception as e:
                logger.warning(
                    "Failed to parse party Pokemon %d at offset 0x%X: %s",
                    i,
                    offset,
                    e,
                )

        return party

    def _parse_pc_boxes(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> dict[str, list[Pokemon]]:
        """Parse PC box Pokemon from Sections 5-13.

        Sections 5-13 form a contiguous buffer containing 14 boxes x 30 Pokemon x 80 bytes.
        """
        # Build contiguous PC buffer from sections 5-13
        pc_buffer = bytearray()
        for sec_id in range(5, 14):
            if sec_id not in section_map:
                # Pad with zeros if section is missing
                pc_buffer.extend(b"\x00" * _DATA_SIZE)
                continue
            sec_offset = section_map[sec_id]
            pc_buffer.extend(data[sec_offset : sec_offset + _DATA_SIZE])

        boxes: dict[str, list[Pokemon]] = {}
        total_pc_size = _NUM_BOXES * _POKEMON_PER_BOX * _BOX_POKEMON_SIZE

        # The PC buffer starts with a 4-byte header (current box number u32).
        # Pokemon data begins immediately after this header.
        pc_data_start = 4

        for box_idx in range(_NUM_BOXES):
            box_name = f"Box {box_idx + 1}"
            box_pokemon: list[Pokemon] = []

            for slot in range(_POKEMON_PER_BOX):
                offset = pc_data_start + (box_idx * _POKEMON_PER_BOX + slot) * _BOX_POKEMON_SIZE
                if offset + _BOX_POKEMON_SIZE > len(pc_buffer):
                    break

                pkmn_data = bytes(pc_buffer[offset : offset + _BOX_POKEMON_SIZE])

                # Skip empty slots (PID == 0 and species == 0 typically)
                pid = struct.unpack_from("<I", pkmn_data, 0)[0]
                if pid == 0:
                    continue

                try:
                    pkmn = self._parse_pokemon(
                        pkmn_data, is_party=False, location=box_name
                    )
                    if pkmn is not None:
                        box_pokemon.append(pkmn)
                except Exception as e:
                    logger.warning(
                        "Failed to parse box %d slot %d: %s",
                        box_idx + 1,
                        slot,
                        e,
                    )

            boxes[box_name] = box_pokemon

        return boxes

    def _parse_pokemon(
        self, pkmn_data: bytes, is_party: bool, location: str
    ) -> Pokemon | None:
        """Parse a single Gen 3 Pokemon from raw bytes.

        Args:
            pkmn_data: 80 bytes (box) or 100 bytes (party).
            is_party: Whether this is party data (has battle stats).
            location: Location string for the Pokemon model.

        Returns:
            A Pokemon model, or None if the slot is empty/invalid.
        """
        expected_size = _PARTY_POKEMON_SIZE if is_party else _BOX_POKEMON_SIZE
        if len(pkmn_data) < expected_size:
            return None

        # --- Unencrypted header (32 bytes) ---
        pid = struct.unpack_from("<I", pkmn_data, 0x00)[0]
        otid = struct.unpack_from("<I", pkmn_data, 0x04)[0]

        # Skip empty slots
        if pid == 0 and otid == 0:
            return None

        nickname_raw = pkmn_data[0x08:0x12]  # 10 bytes
        language = struct.unpack_from("<H", pkmn_data, 0x12)[0]
        ot_name_raw = pkmn_data[0x14:0x1B]   # 7 bytes
        markings = pkmn_data[0x1B]
        stored_checksum = struct.unpack_from("<H", pkmn_data, 0x1C)[0]

        # --- Decrypt substructure data (48 bytes at 0x20) ---
        encrypted = pkmn_data[0x20:0x50]
        try:
            decrypted = decrypt_pokemon_data(encrypted, pid, otid)
        except Exception as e:
            logger.warning("Decryption failed for Pokemon PID=0x%08X: %s", pid, e)
            return None

        # Validate checksum
        computed_checksum = pokemon_checksum(decrypted)
        if computed_checksum != stored_checksum:
            logger.warning(
                "Pokemon PID=0x%08X checksum mismatch "
                "(stored=0x%04X, computed=0x%04X). Data may be corrupt.",
                pid,
                stored_checksum,
                computed_checksum,
            )
            # Continue parsing anyway -- some emulators produce slightly off checksums

        # --- Unshuffle substructures ---
        g_off, a_off, e_off, m_off = get_substructure_order(pid)

        growth = decrypted[g_off : g_off + _SUBSTRUCTURE_SIZE]
        attacks = decrypted[a_off : a_off + _SUBSTRUCTURE_SIZE]
        evs_data = decrypted[e_off : e_off + _SUBSTRUCTURE_SIZE]
        misc = decrypted[m_off : m_off + _SUBSTRUCTURE_SIZE]

        # --- Growth substructure ---
        species_id_raw = struct.unpack_from("<H", growth, 0x00)[0]
        held_item_id = struct.unpack_from("<H", growth, 0x02)[0]
        experience = struct.unpack_from("<I", growth, 0x04)[0]
        pp_bonuses = growth[0x08]
        friendship = growth[0x09]

        if species_id_raw == 0:
            return None

        # Convert Gen 3 internal species ID to National Dex number
        species_id = gen3_species_to_national(species_id_raw)
        if species_id == 0:
            logger.warning(
                "Unknown Gen 3 species internal ID %d for PID=0x%08X",
                species_id_raw,
                pid,
            )
            return None

        # --- Attacks substructure ---
        move_ids = [
            struct.unpack_from("<H", attacks, i * 2)[0] for i in range(4)
        ]
        move_pps = [attacks[0x08 + i] for i in range(4)]

        # --- EVs/Condition substructure ---
        ev_hp = evs_data[0x00]
        ev_atk = evs_data[0x01]
        ev_def = evs_data[0x02]
        ev_spd = evs_data[0x03]
        ev_spa = evs_data[0x04]
        ev_spd_def = evs_data[0x05]

        # --- Misc substructure ---
        pokerus_byte = misc[0x00]
        met_location = misc[0x01]
        origins_info = struct.unpack_from("<H", misc, 0x02)[0]
        iv_bitfield = struct.unpack_from("<I", misc, 0x04)[0]

        # Parse origins info
        met_level = origins_info & 0x7F
        game_origin = (origins_info >> 7) & 0xF
        ball_index = (origins_info >> 11) & 0xF
        ot_gender_bit = (origins_info >> 15) & 0x1

        # Parse IV bitfield
        iv_hp = iv_bitfield & 0x1F
        iv_atk = (iv_bitfield >> 5) & 0x1F
        iv_def = (iv_bitfield >> 10) & 0x1F
        iv_spd = (iv_bitfield >> 15) & 0x1F
        iv_spa = (iv_bitfield >> 20) & 0x1F
        iv_spd_def = (iv_bitfield >> 25) & 0x1F
        is_egg = bool((iv_bitfield >> 30) & 0x1)
        ability_bit = (iv_bitfield >> 31) & 0x1

        # --- Derived values ---
        tid = otid & 0xFFFF
        sid = (otid >> 16) & 0xFFFF

        # Nature: PID % 25
        nature_id = pid % 25

        # Shiny check: (tid ^ sid ^ (pid >> 16) ^ (pid & 0xFFFF)) < 8
        shiny_val = tid ^ sid ^ ((pid >> 16) & 0xFFFF) ^ (pid & 0xFFFF)
        is_shiny = shiny_val < 8

        # Pokerus: non-zero means infected/cured
        has_pokerus = pokerus_byte != 0

        # Decode strings
        nickname = decode_string(nickname_raw)
        ot_name = decode_string(ot_name_raw)

        # Species name
        species_name = _safe_species_name(species_id)

        # Build moves list
        moves: list[Move] = []
        for i in range(4):
            if move_ids[i] != 0:
                moves.append(
                    Move(
                        name=_safe_move_name(move_ids[i]),
                        pp=move_pps[i],
                    )
                )

        # Held item
        held_item = _safe_item_name(held_item_id) if held_item_id != 0 else None

        # Ball name
        pokeball = _BALL_NAMES.get(ball_index, f"Ball #{ball_index}")

        # Met location name
        met_loc_name = _safe_location_name(met_location)

        # Nature name
        nature_name = _safe_nature_name(nature_id)

        # Ability: the ability_bit selects between the species' two abilities.
        # We cannot resolve the actual ability name without a species->ability
        # table, so we store the bit as a placeholder description.
        ability_name = f"Ability slot {ability_bit + 1}"
        try:
            from pokesave.data.abilities import ABILITY_NAMES
            # If we had a species->ability mapping we would use it here.
            # For now, just note the slot.
        except ImportError:
            pass

        # --- Party-only stats ---
        level = 0
        hp = None
        max_hp = None
        stats = None

        if is_party and len(pkmn_data) >= _PARTY_POKEMON_SIZE:
            # Party extension at offset 0x50
            # 0x50: Status condition (u32)
            # 0x54: Level (u8)
            # 0x55: Pokerus remaining (u8)
            # 0x56: Current HP (u16)
            # 0x58: Max HP (u16)
            # 0x5A: Atk (u16), 0x5C: Def (u16), 0x5E: Spd (u16)
            # 0x60: SpA (u16), 0x62: SpD (u16)
            level = pkmn_data[0x54]
            hp = struct.unpack_from("<H", pkmn_data, 0x56)[0]
            max_hp = struct.unpack_from("<H", pkmn_data, 0x58)[0]
            stat_atk = struct.unpack_from("<H", pkmn_data, 0x5A)[0]
            stat_def = struct.unpack_from("<H", pkmn_data, 0x5C)[0]
            stat_spd = struct.unpack_from("<H", pkmn_data, 0x5E)[0]
            stat_spa = struct.unpack_from("<H", pkmn_data, 0x60)[0]
            stat_spd_def = struct.unpack_from("<H", pkmn_data, 0x62)[0]

            stats = Stats(
                hp=max_hp,
                attack=stat_atk,
                defense=stat_def,
                speed=stat_spd,
                sp_attack=stat_spa,
                sp_defense=stat_spd_def,
            )
        else:
            # For box Pokemon, derive level from experience and species
            # (approximate -- would need growth rate tables for exact calc).
            # Use a simple cubic root approximation as a fallback.
            level = self._estimate_level(experience)

        return Pokemon(
            species=species_name,
            species_id=species_id,
            nickname=nickname if nickname != species_name else None,
            level=level,
            moves=moves,
            hp=hp,
            max_hp=max_hp,
            stats=stats,
            evs=EVs(
                hp=ev_hp,
                attack=ev_atk,
                defense=ev_def,
                speed=ev_spd,
                sp_attack=ev_spa,
                sp_defense=ev_spd_def,
            ),
            ivs=IVs(
                hp=iv_hp,
                attack=iv_atk,
                defense=iv_def,
                speed=iv_spd,
                sp_attack=iv_spa,
                sp_defense=iv_spd_def,
            ),
            held_item=held_item,
            ability=ability_name,
            nature=nature_name,
            friendship=friendship,
            ot_name=ot_name,
            ot_id=tid,
            met_location=met_loc_name,
            met_level=met_level,
            pokeball=pokeball,
            pokerus=has_pokerus,
            is_shiny=is_shiny,
            is_egg=is_egg,
            location=location,
        )

    def _estimate_level(self, experience: int) -> int:
        """Estimate Pokemon level from experience points using medium-fast growth.

        This is a rough approximation. The actual level depends on the species'
        growth rate group. Medium Fast (n^3) is the most common, so we use that
        as a default.
        """
        if experience <= 0:
            return 1
        # Medium Fast: exp = n^3
        level = int(round(experience ** (1.0 / 3.0)))
        return max(1, min(100, level))

    def _parse_bag(
        self, data: bytes, section_map: dict[int, int], game: str
    ) -> dict[str, list[Item]]:
        """Parse bag items from Section 1.

        Each item entry is 4 bytes: item_id (u16) + quantity (u16).
        In Emerald and FRLG, the quantity is XOR-encrypted with the lower
        16 bits of the Security Key.
        """
        bag: dict[str, list[Item]] = {}
        pocket_names = ["Items", "Key Items", "Poke Balls", "TMs/HMs", "Berries"]
        for name in pocket_names:
            bag[name] = []

        if 1 not in section_map:
            return bag

        base = section_map[1]
        security_key = self._get_security_key(data, section_map, game)
        qty_key = security_key & 0xFFFF

        # Pocket offsets and max slots vary by game.
        # Format: (pocket_name, offset_from_section1, max_items)
        if "Emerald" in game:
            pockets = [
                ("Items",      0x0560, 30),
                ("Key Items",  0x05D8, 30),
                ("Poke Balls", 0x0650, 16),
                ("TMs/HMs",    0x0690, 64),
                ("Berries",    0x0790, 46),
            ]
        elif "FireRed" in game or "LeafGreen" in game:
            pockets = [
                ("Items",      0x0310, 42),
                ("Key Items",  0x03B8, 30),
                ("Poke Balls", 0x0430, 13),
                ("TMs/HMs",    0x0464, 58),
                ("Berries",    0x054C, 43),
            ]
        else:
            # Ruby/Sapphire
            pockets = [
                ("Items",      0x0560, 20),
                ("Key Items",  0x05B0, 20),
                ("Poke Balls", 0x0600, 16),
                ("TMs/HMs",    0x0640, 64),
                ("Berries",    0x0740, 46),
            ]

        for pocket_name, pocket_offset, max_items in pockets:
            items: list[Item] = []
            for i in range(max_items):
                entry_offset = base + pocket_offset + i * 4
                if entry_offset + 4 > len(data):
                    break

                item_id = struct.unpack_from("<H", data, entry_offset)[0]
                raw_qty = struct.unpack_from("<H", data, entry_offset + 2)[0]

                if item_id == 0:
                    continue

                quantity = (raw_qty ^ qty_key) & 0xFFFF
                item_name = _safe_item_name(item_id)
                items.append(Item(name=item_name, quantity=quantity))

            bag[pocket_name] = items

        return bag
