"""Gen IV save file parser (Diamond/Pearl/Platinum/HeartGold/SoulSilver).

Gen 4 saves are 512 KiB (0x80000 bytes) with two block pairs. Each pair
consists of a small block (trainer/party data) and a big block (PC storage).

Pokemon data uses PRNG-seeded XOR encryption (seed=checksum for block data,
seed=PID for battle stats) and 24 block permutations.

Save-level integrity uses CRC-16-CCITT.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_IV)
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_IV)
  - PKHeX.Core SAV4.cs, PokeCrypto4.cs
"""

from __future__ import annotations

import logging
import struct

from pokesave.crypto.gen4 import (
    crc16_ccitt,
    decrypt_battle_stats,
    decrypt_pokemon_blocks,
    get_block_order,
    pokemon_checksum,
)
from pokesave.data.natures import NATURE_NAMES
from pokesave.data.species import SPECIES_NAMES
from pokesave.encoding.gen4 import decode_string
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

_SAVE_SIZE = 0x80000  # 512 KiB

# Block size definitions per game variant
# GeneralSize (small block), StorageSize (big block)
_DP_SMALL = 0xC100
_DP_BIG = 0x121E0
_PT_SMALL = 0xCF2C
_PT_BIG = 0x121E4
_HGSS_SMALL = 0xF628
_HGSS_BIG = 0x12310

# Backup blocks start at 0x40000
_BACKUP_OFFSET = 0x40000

# Footer sizes (last N bytes of each block)
_FOOTER_SIZE_SINNOH = 0x14  # DP / Platinum: 20-byte footer
_FOOTER_SIZE_HGSS = 0x10    # HGSS: 16-byte footer

# HGSS has a gap between General and Storage blocks
_HGSS_STORAGE_OFFSET = 0xF700  # Storage block starts at this offset within each partition

# Pokemon data sizes
_BOX_POKEMON_SIZE = 136
_PARTY_POKEMON_SIZE = 236
_BLOCK_DATA_SIZE = 128    # 4 x 32-byte blocks
_BATTLE_STATS_SIZE = 100
_SINGLE_BLOCK_SIZE = 32

# PC box constants
_NUM_BOXES = 18
_POKEMON_PER_BOX = 30

# Party offsets within small block (approximate, game-specific)
_DP_PARTY_OFFSET = 0x94
_PT_PARTY_OFFSET = 0x9C
_HGSS_PARTY_OFFSET = 0x94

# PC storage offset within big block
_PC_OFFSET = 0x04
_HGSS_PC_OFFSET = 0x88

# Trainer name offsets in small block
_DP_TRAINER_NAME_OFFSET = 0x64
_PT_TRAINER_NAME_OFFSET = 0x68
_HGSS_TRAINER_NAME_OFFSET = 0x64

# Trainer ID offsets
_DP_TID_OFFSET = 0x74
_PT_TID_OFFSET = 0x78
_HGSS_TID_OFFSET = 0x74

# Ball names
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
    13: "Dusk Ball",
    14: "Heal Ball",
    15: "Quick Ball",
    16: "Cherish Ball",
    # Sport/Park Ball and others
    17: "Park Ball",
    18: "Sport Ball",
}


def _safe_species_name(species_id: int) -> str:
    """Look up species name with fallback for unknown IDs."""
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
        from pokesave.data.items import GEN4_ITEMS
        return GEN4_ITEMS.get(item_id, f"Item #{item_id}")
    except ImportError:
        return f"Item #{item_id}"


def _safe_location_name(loc_id: int) -> str:
    """Look up location name with fallback."""
    try:
        from pokesave.data.locations import GEN4_LOCATIONS
        return GEN4_LOCATIONS.get(loc_id, f"Location #{loc_id}")
    except ImportError:
        return f"Location #{loc_id}"


def _safe_nature_name(nature_id: int) -> str:
    """Look up nature name with fallback."""
    return NATURE_NAMES.get(nature_id, f"Nature #{nature_id}")


class Gen4Parser(BaseParser):
    """Parser for Generation IV Pokemon save files."""

    def parse(self, data: bytes) -> SaveFile:
        """Parse a Gen 4 save file into a structured SaveFile model."""
        if len(data) != _SAVE_SIZE:
            raise ValueError(
                f"Gen 4 save file must be 524288 bytes (512 KiB), got {len(data)}"
            )

        game = self.detect_version(data)
        small_size, big_size = self._get_block_sizes(game)

        # Determine active save by comparing save counters
        active_small_offset, active_big_offset = self._get_active_offsets(
            data, small_size, big_size, game
        )

        # Extract active blocks
        small_block = data[active_small_offset : active_small_offset + small_size]
        big_block = data[active_big_offset : active_big_offset + big_size]

        # Parse trainer
        trainer = self._parse_trainer(small_block, game)

        # Parse party
        party = self._parse_party(small_block, game)

        # Parse PC boxes
        boxes = self._parse_pc_boxes(big_block, game)

        # Bag (simplified)
        bag = self._parse_bag(small_block, game)

        return SaveFile(
            generation=4,
            game=game,
            trainer=trainer,
            party=party,
            boxes=boxes,
            bag=bag,
        )

    def validate_checksum(self, data: bytes) -> bool:
        """Validate CRC-16-CCITT checksums on the save blocks."""
        game = self.detect_version(data)
        small_size, big_size = self._get_block_sizes(game)
        footer_size = self._get_footer_size(game)
        storage_offset = self._get_storage_offset(game, small_size)

        # CRC is always at the last 2 bytes of the block (footer_end - 2)
        crc_rel = footer_size - 2

        all_valid = True

        # Validate both primary and backup blocks
        for base in (0, _BACKUP_OFFSET):
            # Small block CRC
            small_start = base
            footer_start = small_start + small_size - footer_size
            if footer_start + footer_size <= len(data):
                stored_crc = struct.unpack_from("<H", data, footer_start + crc_rel)[0]
                block_data = data[small_start : small_start + small_size - footer_size]
                computed_crc = crc16_ccitt(block_data)
                if stored_crc != computed_crc:
                    logger.warning(
                        "Small block CRC mismatch at base 0x%X "
                        "(stored=0x%04X, computed=0x%04X)",
                        base,
                        stored_crc,
                        computed_crc,
                    )
                    all_valid = False

            # Big block CRC
            big_start = base + storage_offset
            big_footer_start = big_start + big_size - footer_size
            if big_footer_start + footer_size <= len(data):
                stored_crc = struct.unpack_from("<H", data, big_footer_start + crc_rel)[0]
                block_data = data[big_start : big_start + big_size - footer_size]
                computed_crc = crc16_ccitt(block_data)
                if stored_crc != computed_crc:
                    logger.warning(
                        "Big block CRC mismatch at base 0x%X "
                        "(stored=0x%04X, computed=0x%04X)",
                        base,
                        stored_crc,
                        computed_crc,
                    )
                    all_valid = False

        return all_valid

    def detect_version(self, data: bytes) -> str:
        """Detect the specific Gen 4 game version.

        Checks the backup block footer at 0x40000 for GeneralSize and SDK magic.
        """
        if self._check_footer(data, _DP_SMALL):
            return "Diamond/Pearl"
        if self._check_footer(data, _PT_SMALL):
            return "Platinum"
        if self._check_footer(data, _HGSS_SMALL):
            return "HeartGold/SoulSilver"
        return "Unknown Gen 4"

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _check_footer(self, data: bytes, general_size: int) -> bool:
        """Check if the footer matches the expected GeneralSize.

        Checks both primary (0x0) and backup (0x40000) blocks. The footer
        at offset general_size - 0xC stores the block size, and the SDK
        date stamp at general_size - 0x8 must be non-zero.
        """
        for block_base in (0x0, _BACKUP_OFFSET):
            footer_offset = block_base + general_size
            size_offset = footer_offset - 0xC
            stamp_offset = footer_offset - 0x8

            if size_offset + 4 > len(data) or size_offset < 0:
                continue

            block_size = struct.unpack_from("<I", data, size_offset)[0]
            if block_size != general_size:
                continue

            if stamp_offset + 4 <= len(data):
                stamp = struct.unpack_from("<I", data, stamp_offset)[0]
                if stamp != 0:
                    return True

        return False

    def _get_block_sizes(self, game: str) -> tuple[int, int]:
        """Return (small_block_size, big_block_size) for the given game."""
        if "Diamond" in game or "Pearl" in game:
            return (_DP_SMALL, _DP_BIG)
        if "Platinum" in game:
            return (_PT_SMALL, _PT_BIG)
        if "HeartGold" in game or "SoulSilver" in game:
            return (_HGSS_SMALL, _HGSS_BIG)
        # Default to DP
        return (_DP_SMALL, _DP_BIG)

    def _get_footer_size(self, game: str) -> int:
        """Return the footer size for the given game."""
        if "HeartGold" in game or "SoulSilver" in game:
            return _FOOTER_SIZE_HGSS
        return _FOOTER_SIZE_SINNOH

    def _get_storage_offset(self, game: str, small_size: int) -> int:
        """Return the storage block offset within a partition.

        For DP/Pt the storage block immediately follows the general block.
        For HGSS there is a gap; the storage block starts at 0xF700.
        """
        if "HeartGold" in game or "SoulSilver" in game:
            return _HGSS_STORAGE_OFFSET
        return small_size

    def _get_active_offsets(
        self, data: bytes, small_size: int, big_size: int, game: str
    ) -> tuple[int, int]:
        """Determine active save block offsets by comparing save counters.

        Returns (small_block_offset, big_block_offset) for the active save.
        """
        footer_size = self._get_footer_size(game)
        storage_offset = self._get_storage_offset(game, small_size)

        # Save counter location within the footer differs by game:
        # DP/Pt (20-byte footer): save counter at footer_start + 0x04
        # HGSS (16-byte footer): save counter at footer_start + 0x00
        if "HeartGold" in game or "SoulSilver" in game:
            counter_rel = 0x00
        else:
            counter_rel = 0x04

        primary_footer = small_size - footer_size
        backup_footer = _BACKUP_OFFSET + small_size - footer_size

        primary_counter = 0
        backup_counter = 0

        if primary_footer + footer_size <= len(data):
            primary_counter = struct.unpack_from("<I", data, primary_footer + counter_rel)[0]
        if backup_footer + footer_size <= len(data):
            backup_counter = struct.unpack_from("<I", data, backup_footer + counter_rel)[0]

        if backup_counter > primary_counter:
            return (_BACKUP_OFFSET, _BACKUP_OFFSET + storage_offset)
        return (0, storage_offset)

    def _get_party_offset(self, game: str) -> int:
        """Get the party data offset within the small block."""
        if "Platinum" in game:
            return _PT_PARTY_OFFSET
        if "HeartGold" in game or "SoulSilver" in game:
            return _HGSS_PARTY_OFFSET
        return _DP_PARTY_OFFSET

    def _get_trainer_offsets(self, game: str) -> tuple[int, int]:
        """Return (name_offset, tid_offset) for the given game."""
        if "Platinum" in game:
            return (_PT_TRAINER_NAME_OFFSET, _PT_TID_OFFSET)
        if "HeartGold" in game or "SoulSilver" in game:
            return (_HGSS_TRAINER_NAME_OFFSET, _HGSS_TID_OFFSET)
        return (_DP_TRAINER_NAME_OFFSET, _DP_TID_OFFSET)

    def _parse_trainer(self, small_block: bytes, game: str) -> Trainer:
        """Parse trainer data from the small block."""
        name_offset, tid_offset = self._get_trainer_offsets(game)

        # Trainer name: 16 bytes (8 chars x 2 bytes, Gen 4 encoding)
        name = decode_string(small_block[name_offset : name_offset + 16])

        # TID and SID: u16 each at tid_offset and tid_offset+2
        tid = struct.unpack_from("<H", small_block, tid_offset)[0]
        sid = struct.unpack_from("<H", small_block, tid_offset + 2)[0]

        # Gender: game-specific fixed offset
        # DP: 0x7C, Platinum: 0x80, HGSS: 0x7C
        if "Platinum" in game:
            gender_offset = 0x80
        else:
            gender_offset = 0x7C
        if gender_offset < len(small_block):
            gender_byte = small_block[gender_offset]
            gender = "Female" if gender_byte == 1 else "Male"
        else:
            gender = "Unknown"

        # Playtime: varies by game
        # DP: offset 0x86, Pt: offset 0x8A, HGSS: 0x86
        # Hours (u16), Minutes (u8), Seconds (u8)
        if "Platinum" in game:
            playtime_offset = 0x8A
        else:
            playtime_offset = 0x86

        hours = 0
        minutes = 0
        seconds = 0
        if playtime_offset + 4 <= len(small_block):
            hours = struct.unpack_from("<H", small_block, playtime_offset)[0]
            minutes = small_block[playtime_offset + 2]
            seconds = small_block[playtime_offset + 3]

        # Money: varies by game
        # DP: 0x78, Pt: 0x7C, HGSS: 0x78
        if "Platinum" in game:
            money_offset = 0x7C
        else:
            money_offset = 0x78
        money = 0
        if money_offset + 4 <= len(small_block):
            money = struct.unpack_from("<I", small_block, money_offset)[0]

        # Badges
        badges = self._parse_badges(small_block, game)

        # Pokedex
        pokedex_owned, pokedex_seen = self._parse_pokedex(small_block, game)

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

    def _parse_badges(self, small_block: bytes, game: str) -> list[str]:
        """Parse badge data from the small block.

        Badge data is a bitmask at offset 0x7E (DP/HGSS) or 0x82 (Pt).
        DP/Pt: 1 byte, bits 0-7 = 8 Sinnoh badges.
        HGSS: 2 bytes, first byte = 8 Johto badges, second byte = 8 Kanto badges.
        """
        if "Platinum" in game:
            badge_offset = 0x82
        else:
            badge_offset = 0x7E

        if "HeartGold" in game or "SoulSilver" in game:
            badge_names_johto = [
                "Zephyr", "Hive", "Plain", "Fog",
                "Storm", "Mineral", "Glacier", "Rising",
            ]
            badge_names_kanto = [
                "Boulder", "Cascade", "Thunder", "Rainbow",
                "Soul", "Marsh", "Volcano", "Earth",
            ]
            if badge_offset + 2 > len(small_block):
                return []
            johto_byte = small_block[badge_offset]
            kanto_byte = small_block[badge_offset + 1]
            badges = []
            for i, name in enumerate(badge_names_johto):
                if johto_byte & (1 << i):
                    badges.append(name)
            for i, name in enumerate(badge_names_kanto):
                if kanto_byte & (1 << i):
                    badges.append(name)
            return badges

        badge_names = [
            "Coal", "Forest", "Cobble", "Fen",
            "Relic", "Mine", "Icicle", "Beacon",
        ]
        if badge_offset + 1 > len(small_block):
            return []
        badge_byte = small_block[badge_offset]
        badges = []
        for i, name in enumerate(badge_names):
            if badge_byte & (1 << i):
                badges.append(name)
        return badges

    def _parse_pokedex(
        self, small_block: bytes, game: str
    ) -> tuple[int, int]:
        """Parse Pokedex owned/seen counts from the small block."""
        # Pokedex offsets are deeply game-specific.
        # For a best-effort parse, we return 0,0 and let exact offsets
        # be filled in with testing against real save files.
        return (0, 0)

    def _parse_party(self, small_block: bytes, game: str) -> list[Pokemon]:
        """Parse party Pokemon from the small block."""
        party_offset = self._get_party_offset(game)

        if party_offset + 4 > len(small_block):
            return []

        # Party count is 4 bytes before the first Pokemon
        party_count = struct.unpack_from("<I", small_block, party_offset)[0]
        if party_count > 6:
            # Try reading as a single byte instead (some games)
            party_count = small_block[party_offset]
            if party_count > 6:
                party_count = 6

        pokemon_start = party_offset + 4
        party = []

        for i in range(party_count):
            offset = pokemon_start + i * _PARTY_POKEMON_SIZE
            if offset + _PARTY_POKEMON_SIZE > len(small_block):
                break

            pkmn_data = small_block[offset : offset + _PARTY_POKEMON_SIZE]
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
        self, big_block: bytes, game: str
    ) -> dict[str, list[Pokemon]]:
        """Parse PC box Pokemon from the big block.

        18 boxes x 30 Pokemon x 136 bytes.
        """
        boxes: dict[str, list[Pokemon]] = {}

        # HGSS has a larger reserved area before box data (0x88 vs 0x04 for DP/Pt)
        if "HeartGold" in game or "SoulSilver" in game:
            pc_data_offset = _HGSS_PC_OFFSET
        else:
            pc_data_offset = _PC_OFFSET

        for box_idx in range(_NUM_BOXES):
            box_name = f"Box {box_idx + 1}"
            box_pokemon: list[Pokemon] = []

            for slot in range(_POKEMON_PER_BOX):
                offset = pc_data_offset + (
                    box_idx * _POKEMON_PER_BOX + slot
                ) * _BOX_POKEMON_SIZE

                if offset + _BOX_POKEMON_SIZE > len(big_block):
                    break

                pkmn_data = big_block[offset : offset + _BOX_POKEMON_SIZE]

                # Skip empty slots
                pid = struct.unpack_from("<I", pkmn_data, 0)[0]
                if pid == 0:
                    # Also check checksum -- some Pokemon have PID=0 but are valid
                    checksum = struct.unpack_from("<H", pkmn_data, 0x06)[0]
                    if checksum == 0:
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
        """Parse a single Gen 4 Pokemon from raw bytes.

        Args:
            pkmn_data: 136 bytes (box) or 236 bytes (party).
            is_party: Whether this is party data (has battle stats).
            location: Location string for the Pokemon model.

        Returns:
            A Pokemon model, or None if the slot is empty/invalid.
        """
        expected_size = _PARTY_POKEMON_SIZE if is_party else _BOX_POKEMON_SIZE
        if len(pkmn_data) < expected_size:
            return None

        # --- Header (8 bytes) ---
        pid = struct.unpack_from("<I", pkmn_data, 0x00)[0]
        # 0x04: unused u16
        stored_checksum = struct.unpack_from("<H", pkmn_data, 0x06)[0]

        # --- Decrypt block data (128 bytes at 0x08-0x87) ---
        encrypted_blocks = pkmn_data[0x08:0x88]
        try:
            decrypted_blocks = decrypt_pokemon_blocks(encrypted_blocks, stored_checksum)
        except Exception as e:
            logger.warning(
                "Block decryption failed for Pokemon PID=0x%08X: %s", pid, e
            )
            return None

        # Validate checksum — skip slots with mismatches (residual/corrupt data)
        computed_checksum = pokemon_checksum(decrypted_blocks)
        if computed_checksum != stored_checksum:
            return None

        # --- Unshuffle blocks ---
        a_off, b_off, c_off, d_off = get_block_order(pid)

        block_a = decrypted_blocks[a_off : a_off + _SINGLE_BLOCK_SIZE]
        block_b = decrypted_blocks[b_off : b_off + _SINGLE_BLOCK_SIZE]
        block_c = decrypted_blocks[c_off : c_off + _SINGLE_BLOCK_SIZE]
        block_d = decrypted_blocks[d_off : d_off + _SINGLE_BLOCK_SIZE]

        # --- Block A: Species, Item, OTID, EXP, Friendship, Ability, etc. ---
        species_id = struct.unpack_from("<H", block_a, 0x00)[0]
        held_item_id = struct.unpack_from("<H", block_a, 0x02)[0]
        otid = struct.unpack_from("<I", block_a, 0x04)[0]
        experience = struct.unpack_from("<I", block_a, 0x08)[0]
        friendship = block_a[0x0C]
        ability_id = block_a[0x0D]
        markings = block_a[0x0E]
        language = block_a[0x0F]

        # EVs at offset 0x10 in block A
        ev_hp = block_a[0x10]
        ev_atk = block_a[0x11]
        ev_def = block_a[0x12]
        ev_spd = block_a[0x13]
        ev_spa = block_a[0x14]
        ev_spd_def = block_a[0x15]

        if species_id == 0:
            return None

        tid = otid & 0xFFFF
        sid = (otid >> 16) & 0xFFFF

        # --- Block B: Moves, PP, IVs ---
        move_ids = [
            struct.unpack_from("<H", block_b, i * 2)[0] for i in range(4)
        ]
        move_pps = [block_b[0x08 + i] for i in range(4)]
        # PP ups packed at offset 0x0C (u32)
        pp_ups = struct.unpack_from("<I", block_b, 0x0C)[0]

        # IV bitfield at offset 0x10 in block B
        iv_bitfield = struct.unpack_from("<I", block_b, 0x10)[0]
        iv_hp = iv_bitfield & 0x1F
        iv_atk = (iv_bitfield >> 5) & 0x1F
        iv_def = (iv_bitfield >> 10) & 0x1F
        iv_spd = (iv_bitfield >> 15) & 0x1F
        iv_spa = (iv_bitfield >> 20) & 0x1F
        iv_spd_def = (iv_bitfield >> 25) & 0x1F
        is_egg = bool((iv_bitfield >> 30) & 0x1)
        is_nicknamed = bool((iv_bitfield >> 31) & 0x1)

        # Forme and gender byte at 0x18 in block B
        forme_gender_byte = block_b[0x18]
        # Nature: derived from PID % 25 in Gen 4
        nature_id = pid % 25

        # --- Block C: Nickname, Origin game ---
        nickname_raw = block_c[0x00:0x16]  # 22 bytes (11 chars)
        # Origin game at offset 0x17
        origin_game_id = block_c[0x17]

        # --- Block D: OT Name, dates, locations ---
        ot_name_raw = block_d[0x00:0x10]  # 16 bytes (8 chars)
        # Egg date at 0x10 (3 bytes: year-2000, month, day)
        # Met date at 0x13 (3 bytes)
        # Egg location at 0x16 (u16)
        egg_location = struct.unpack_from("<H", block_d, 0x16)[0]
        # Met location at 0x18 (u16)
        met_location_id = struct.unpack_from("<H", block_d, 0x18)[0]
        # Pokerus at 0x1A
        pokerus_byte = block_d[0x1A]
        # Pokeball at 0x1B
        ball_id = block_d[0x1B]
        # Met level + OT gender at 0x1C: bits 0-6 = level, bit 7 = OT gender
        met_level_gender = block_d[0x1C]
        met_level = met_level_gender & 0x7F
        ot_gender_bit = (met_level_gender >> 7) & 0x1
        # Encounter type at 0x1D
        encounter_type = block_d[0x1D]

        # --- Derived values ---
        # Shiny: same formula as Gen 3
        shiny_val = tid ^ sid ^ ((pid >> 16) & 0xFFFF) ^ (pid & 0xFFFF)
        is_shiny = shiny_val < 8

        # Pokerus
        has_pokerus = pokerus_byte != 0

        # Decode strings
        nickname = decode_string(nickname_raw)
        ot_name = decode_string(ot_name_raw)

        # Species name
        species_name = _safe_species_name(species_id)

        # Nature name
        nature_name = _safe_nature_name(nature_id)

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
        pokeball = _BALL_NAMES.get(ball_id, f"Ball #{ball_id}")

        # Met location
        met_loc_name = _safe_location_name(met_location_id)

        # Ability name
        try:
            from pokesave.data.abilities import ABILITY_NAMES
            ability_name = ABILITY_NAMES.get(ability_id, f"Ability #{ability_id}")
        except ImportError:
            ability_name = f"Ability #{ability_id}"

        # --- Party-only battle stats ---
        level = 0
        hp = None
        max_hp = None
        stats = None

        if is_party and len(pkmn_data) >= _PARTY_POKEMON_SIZE:
            # Decrypt battle stats (100 bytes at 0x88-0xEB)
            encrypted_stats = pkmn_data[0x88:0xEC]
            try:
                decrypted_stats = decrypt_battle_stats(encrypted_stats, pid)
            except Exception as e:
                logger.warning(
                    "Battle stats decryption failed for PID=0x%08X: %s", pid, e
                )
                decrypted_stats = encrypted_stats

            # Parse battle stats
            # 0x00: Status condition (u32)
            # 0x04: Level (u8)
            # 0x05: Capsule index (u8)
            # 0x06: Current HP (u16)
            # 0x08: Max HP (u16)
            # 0x0A: Atk (u16)
            # 0x0C: Def (u16)
            # 0x0E: Spd (u16)
            # 0x10: SpA (u16)
            # 0x12: SpD (u16)
            level = decrypted_stats[0x04]
            hp = struct.unpack_from("<H", decrypted_stats, 0x06)[0]
            max_hp = struct.unpack_from("<H", decrypted_stats, 0x08)[0]
            stat_atk = struct.unpack_from("<H", decrypted_stats, 0x0A)[0]
            stat_def = struct.unpack_from("<H", decrypted_stats, 0x0C)[0]
            stat_spd = struct.unpack_from("<H", decrypted_stats, 0x0E)[0]
            stat_spa = struct.unpack_from("<H", decrypted_stats, 0x10)[0]
            stat_spd_def = struct.unpack_from("<H", decrypted_stats, 0x12)[0]

            stats = Stats(
                hp=max_hp,
                attack=stat_atk,
                defense=stat_def,
                speed=stat_spd,
                sp_attack=stat_spa,
                sp_defense=stat_spd_def,
            )
        else:
            # Estimate level from EXP for box Pokemon
            level = self._estimate_level(experience)

        return Pokemon(
            species=species_name,
            species_id=species_id,
            nickname=nickname if is_nicknamed else None,
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
        """Estimate Pokemon level from experience using medium-fast growth (n^3)."""
        if experience <= 0:
            return 1
        level = int(round(experience ** (1.0 / 3.0)))
        return max(1, min(100, level))

    def _parse_bag(
        self, small_block: bytes, game: str
    ) -> dict[str, list[Item]]:
        """Parse bag items from the small block.

        Bag layout is deeply game-specific. Returns empty pockets as a
        placeholder until exact offsets are confirmed with real save files.
        """
        pocket_names = [
            "Items", "Medicine", "Poke Balls", "TMs/HMs",
            "Berries", "Mail", "Battle Items", "Key Items",
        ]
        return {name: [] for name in pocket_names}
