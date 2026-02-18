"""Gen V save file parser (Black/White/Black 2/White 2).

Gen 5 saves are 512 KiB (0x80000 bytes). Structurally similar to Gen 4 with
key differences:
  - Nature is stored explicitly (not derived from PID)
  - Hidden Ability flag at Block B offset 0x1A
  - Battle stats are 84 bytes (not 100)
  - Party Pokemon are 220 bytes (not 236)
  - Character encoding is UTF-16-LE (standard Unicode)
  - 24 PC boxes (not 18)

References:
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_V)
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_V)
  - PKHeX.Core SAV5.cs, PokeCrypto5.cs
"""

from __future__ import annotations

import logging
import struct

from pokesave.crypto.gen5 import (
    crc16_ccitt,
    decrypt_battle_stats,
    decrypt_pokemon_blocks,
    get_block_order,
    pokemon_checksum,
)
from pokesave.data.natures import NATURE_NAMES
from pokesave.data.species import SPECIES_NAMES
from pokesave.encoding.gen4 import decode_string_gen5
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

# Main block sizes for game detection
_BW_MAIN_SIZE = 0x24000
_B2W2_MAIN_SIZE = 0x26000

# Info block lengths for CRC validation
_BW_INFO_LENGTH = 0x8C
_B2W2_INFO_LENGTH = 0x94

# Pokemon data sizes
_BOX_POKEMON_SIZE = 136
_PARTY_POKEMON_SIZE = 220   # 136 + 84 battle stats
_BLOCK_DATA_SIZE = 128      # 4 x 32-byte blocks
_BATTLE_STATS_SIZE = 84
_SINGLE_BLOCK_SIZE = 32

# PC box constants
_NUM_BOXES = 24
_POKEMON_PER_BOX = 30

# Party offsets within main block (block 26)
_BW_PARTY_OFFSET = 0x18E00
_B2W2_PARTY_OFFSET = 0x18E00

# Trainer info offsets (block 27)
_BW_TRAINER_NAME_OFFSET = 0x19404
_B2W2_TRAINER_NAME_OFFSET = 0x19404

_BW_TID_OFFSET = 0x19414
_B2W2_TID_OFFSET = 0x19414

# Playtime offset within main block (trainer block + 0x24)
_BW_PLAYTIME_OFFSET = 0x19424
_B2W2_PLAYTIME_OFFSET = 0x19424

# Money offset within main block (block 52: badge/money/misc)
_BW_MONEY_OFFSET = 0x21200
_B2W2_MONEY_OFFSET = 0x21200

# PC storage offset within main block (block 1 starts at 0x400)
# Each box is 0x1000 bytes (30 Pokemon x 136 bytes + 0x10 metadata)
_BW_PC_OFFSET = 0x400
_B2W2_PC_OFFSET = 0x400
_PC_BOX_STRIDE = 0x1000  # 4096 bytes per box (30*136 + 16 gap)

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
    17: "Park Ball",
    18: "Dream Ball",
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
        from pokesave.data.items import GEN5_ITEMS
        return GEN5_ITEMS.get(item_id, f"Item #{item_id}")
    except ImportError:
        return f"Item #{item_id}"


def _safe_location_name(loc_id: int) -> str:
    """Look up location name with fallback."""
    try:
        from pokesave.data.locations import GEN5_LOCATIONS
        return GEN5_LOCATIONS.get(loc_id, f"Location #{loc_id}")
    except ImportError:
        return f"Location #{loc_id}"


def _safe_nature_name(nature_id: int) -> str:
    """Look up nature name with fallback."""
    return NATURE_NAMES.get(nature_id, f"Nature #{nature_id}")


class Gen5Parser(BaseParser):
    """Parser for Generation V Pokemon save files."""

    def parse(self, data: bytes) -> SaveFile:
        """Parse a Gen 5 save file into a structured SaveFile model."""
        if len(data) != _SAVE_SIZE:
            raise ValueError(
                f"Gen 5 save file must be 524288 bytes (512 KiB), got {len(data)}"
            )

        game = self.detect_version(data)
        main_size = self._get_main_size(game)

        # The primary save block is at offset 0x0.
        # The backup block is at offset 0x40000 (but Gen 5 does not use the
        # same dual-block structure as Gen 4 -- it uses a single main block
        # with a CRC footer).
        # For simplicity, parse from offset 0x0 using the main block size.
        main_block = data[0 : main_size]

        # Parse trainer
        trainer = self._parse_trainer(main_block, game)

        # Parse party
        party = self._parse_party(main_block, game)

        # Parse PC boxes
        boxes = self._parse_pc_boxes(main_block, game)

        # Bag
        bag = self._parse_bag(main_block, game)

        return SaveFile(
            generation=5,
            game=game,
            trainer=trainer,
            party=party,
            boxes=boxes,
            bag=bag,
        )

    def validate_checksum(self, data: bytes) -> bool:
        """Validate CRC-16-CCITT checksums for the save file."""
        game = self.detect_version(data)
        main_size = self._get_main_size(game)
        info_length = self._get_info_length(game)

        # Footer is at main_size - 0x100
        footer_offset = main_size - 0x100
        if footer_offset < 0 or footer_offset + info_length > len(data):
            logger.warning("Footer offset out of bounds for Gen 5 validation")
            return False

        # The footer slice is info_length + 0x10 bytes.
        # CRC is at the last 2 bytes of that slice (offset info_length + 0x0E).
        crc_offset = footer_offset + info_length + 0x0E
        if crc_offset + 2 > len(data):
            return False

        stored_crc = struct.unpack_from("<H", data, crc_offset)[0]

        # Compute CRC over the first info_length bytes of the footer
        info_data = data[footer_offset : footer_offset + info_length]
        computed_crc = crc16_ccitt(info_data)

        if stored_crc != computed_crc:
            logger.warning(
                "Gen 5 footer CRC mismatch (stored=0x%04X, computed=0x%04X)",
                stored_crc,
                computed_crc,
            )
            return False

        return True

    def detect_version(self, data: bytes) -> str:
        """Detect whether this is Black/White or Black 2/White 2.

        Uses CRC validation on the footer at the expected main_size.
        """
        if self._validate_footer(data, _BW_MAIN_SIZE, _BW_INFO_LENGTH):
            return "Black/White"
        if self._validate_footer(data, _B2W2_MAIN_SIZE, _B2W2_INFO_LENGTH):
            return "Black 2/White 2"
        return "Unknown Gen 5"

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _validate_footer(
        self, data: bytes, main_size: int, info_length: int
    ) -> bool:
        """Check if a Gen 5 footer at the given main_size is valid.

        The footer slice is info_length + 0x10 bytes starting at main_size - 0x100.
        The CRC-16 is stored at the last 2 bytes of that slice (offset info_length + 0x0E).
        The CRC is computed over the first info_length bytes.
        """
        footer_offset = main_size - 0x100
        if footer_offset < 0 or footer_offset + info_length + 0x10 > len(data):
            return False

        crc_offset = footer_offset + info_length + 0x0E
        if crc_offset + 2 > len(data):
            return False

        stored_crc = struct.unpack_from("<H", data, crc_offset)[0]
        info_data = data[footer_offset : footer_offset + info_length]
        computed_crc = crc16_ccitt(info_data)

        return stored_crc == computed_crc

    def _get_main_size(self, game: str) -> int:
        """Return the main block size for the given game."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_MAIN_SIZE
        return _BW_MAIN_SIZE

    def _get_info_length(self, game: str) -> int:
        """Return the info block length for the given game."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_INFO_LENGTH
        return _BW_INFO_LENGTH

    def _get_party_offset(self, game: str) -> int:
        """Get the party data offset within the main block."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_PARTY_OFFSET
        return _BW_PARTY_OFFSET

    def _get_trainer_offsets(self, game: str) -> tuple[int, int]:
        """Return (name_offset, tid_offset) for the given game."""
        if "Black 2" in game or "White 2" in game:
            return (_B2W2_TRAINER_NAME_OFFSET, _B2W2_TID_OFFSET)
        return (_BW_TRAINER_NAME_OFFSET, _BW_TID_OFFSET)

    def _get_pc_offset(self, game: str) -> int:
        """Return PC storage offset within the main block."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_PC_OFFSET
        return _BW_PC_OFFSET

    def _get_playtime_offset(self, game: str) -> int:
        """Return playtime offset within the main block."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_PLAYTIME_OFFSET
        return _BW_PLAYTIME_OFFSET

    def _get_money_offset(self, game: str) -> int:
        """Return money offset within the main block."""
        if "Black 2" in game or "White 2" in game:
            return _B2W2_MONEY_OFFSET
        return _BW_MONEY_OFFSET

    def _parse_trainer(self, main_block: bytes, game: str) -> Trainer:
        """Parse trainer data from the main block."""
        name_offset, tid_offset = self._get_trainer_offsets(game)

        # Trainer name: 16 bytes (8 chars in UTF-16-LE)
        if name_offset + 16 <= len(main_block):
            name = decode_string_gen5(main_block[name_offset : name_offset + 16])
        else:
            name = "Unknown"

        # TID and SID
        tid = 0
        sid = 0
        if tid_offset + 4 <= len(main_block):
            tid = struct.unpack_from("<H", main_block, tid_offset)[0]
            sid = struct.unpack_from("<H", main_block, tid_offset + 2)[0]

        # Gender: at trainer block offset + 0x21
        gender_offset = name_offset + 0x21
        if gender_offset < len(main_block):
            gender_byte = main_block[gender_offset]
            gender = "Female" if gender_byte == 1 else "Male"
        else:
            gender = "Unknown"

        # Playtime: hours (u16), minutes (u8), seconds (u8)
        playtime_offset = self._get_playtime_offset(game)
        hours = 0
        minutes = 0
        seconds = 0
        if playtime_offset + 4 <= len(main_block):
            hours = struct.unpack_from("<H", main_block, playtime_offset)[0]
            minutes = main_block[playtime_offset + 2]
            seconds = main_block[playtime_offset + 3]

        # Money: stored in block 52 (badge/money/misc)
        money_offset = self._get_money_offset(game)
        money = 0
        if 0 <= money_offset and money_offset + 4 <= len(main_block):
            money = struct.unpack_from("<I", main_block, money_offset)[0]

        # Badges and Pokedex -- game-specific offsets
        badges = self._parse_badges(main_block, game)
        pokedex_owned, pokedex_seen = self._parse_pokedex(main_block, game)

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

    def _parse_badges(self, main_block: bytes, game: str) -> list[str]:
        """Parse badge data. Exact offsets are game-specific."""
        badge_names = [
            "Trio", "Basic", "Insect", "Bolt",
            "Quake", "Jet", "Freeze", "Legend",
        ]
        # Badge offset is deeply game-specific; placeholder return
        return []

    def _parse_pokedex(
        self, main_block: bytes, game: str
    ) -> tuple[int, int]:
        """Parse Pokedex owned/seen counts."""
        # Offsets are game-specific; return placeholder
        return (0, 0)

    def _parse_party(self, main_block: bytes, game: str) -> list[Pokemon]:
        """Parse party Pokemon from the main block."""
        party_offset = self._get_party_offset(game)

        if party_offset + 8 > len(main_block):
            return []

        # Party block has an 8-byte header: u32 count + u32 secondary field
        party_count = struct.unpack_from("<I", main_block, party_offset)[0]
        if party_count > 6:
            party_count = 6

        pokemon_start = party_offset + 8
        party: list[Pokemon] = []

        for i in range(party_count):
            offset = pokemon_start + i * _PARTY_POKEMON_SIZE
            if offset + _PARTY_POKEMON_SIZE > len(main_block):
                break

            pkmn_data = main_block[offset : offset + _PARTY_POKEMON_SIZE]
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
        self, main_block: bytes, game: str
    ) -> dict[str, list[Pokemon]]:
        """Parse PC box Pokemon from the main block.

        24 boxes x 30 Pokemon x 136 bytes.
        """
        boxes: dict[str, list[Pokemon]] = {}
        pc_offset = self._get_pc_offset(game)

        for box_idx in range(_NUM_BOXES):
            box_name = f"Box {box_idx + 1}"
            box_pokemon: list[Pokemon] = []

            for slot in range(_POKEMON_PER_BOX):
                # Each box is 0x1000 bytes: 30 * 136 bytes of Pokemon + 0x10 metadata
                offset = pc_offset + box_idx * _PC_BOX_STRIDE + slot * _BOX_POKEMON_SIZE

                if offset + _BOX_POKEMON_SIZE > len(main_block):
                    break

                pkmn_data = main_block[offset : offset + _BOX_POKEMON_SIZE]

                # Skip empty slots
                pid = struct.unpack_from("<I", pkmn_data, 0)[0]
                if pid == 0:
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
        """Parse a single Gen 5 Pokemon from raw bytes.

        Args:
            pkmn_data: 136 bytes (box) or 220 bytes (party).
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

        # Validate checksum
        computed_checksum = pokemon_checksum(decrypted_blocks)
        if computed_checksum != stored_checksum:
            logger.warning(
                "Pokemon PID=0x%08X checksum mismatch "
                "(stored=0x%04X, computed=0x%04X). Data may be corrupt.",
                pid,
                stored_checksum,
                computed_checksum,
            )

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

        # --- Block B: Moves, PP, IVs, Nature (explicit!), Hidden Ability ---
        move_ids = [
            struct.unpack_from("<H", block_b, i * 2)[0] for i in range(4)
        ]
        move_pps = [block_b[0x08 + i] for i in range(4)]
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

        # Forme and gender byte at 0x18
        forme_gender_byte = block_b[0x18]

        # **KEY GEN 5 DIFFERENCE**: Nature is stored explicitly at 0x19 in block B
        nature_id = block_b[0x19]

        # Hidden Ability flag at 0x1A in block B
        hidden_ability_flag = block_b[0x1A]
        has_hidden_ability = bool(hidden_ability_flag & 0x01)

        # --- Block C: Nickname, Origin game ---
        nickname_raw = block_c[0x00:0x16]  # 22 bytes (11 UTF-16 chars)
        origin_game_id = block_c[0x17]

        # --- Block D: OT Name, dates, locations ---
        ot_name_raw = block_d[0x00:0x10]  # 16 bytes (8 UTF-16 chars)
        # Egg date at 0x10 (3 bytes)
        # Met date at 0x13 (3 bytes)
        # Egg location at 0x16 (u16)
        egg_location = struct.unpack_from("<H", block_d, 0x16)[0]
        # Met location at 0x18 (u16)
        met_location_id = struct.unpack_from("<H", block_d, 0x18)[0]
        # Pokerus at 0x1A
        pokerus_byte = block_d[0x1A]
        # Pokeball at 0x1B
        ball_id = block_d[0x1B]
        # Met level + OT gender at 0x1C
        met_level_gender = block_d[0x1C]
        met_level = met_level_gender & 0x7F
        ot_gender_bit = (met_level_gender >> 7) & 0x1
        # Encounter type at 0x1D
        encounter_type = block_d[0x1D]

        # --- Derived values ---
        # Shiny: same formula as Gen 3/4
        shiny_val = tid ^ sid ^ ((pid >> 16) & 0xFFFF) ^ (pid & 0xFFFF)
        is_shiny = shiny_val < 8

        # Pokerus
        has_pokerus = pokerus_byte != 0

        # Decode strings using Gen 5 UTF-16-LE decoder
        nickname = decode_string_gen5(nickname_raw)
        ot_name = decode_string_gen5(ot_name_raw)

        # Species name
        species_name = _safe_species_name(species_id)

        # Nature name (from explicit byte, NOT PID)
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
        ability_label = ""
        try:
            from pokesave.data.abilities import ABILITY_NAMES
            ability_label = ABILITY_NAMES.get(ability_id, f"Ability #{ability_id}")
        except ImportError:
            ability_label = f"Ability #{ability_id}"

        if has_hidden_ability:
            ability_label += " (Hidden)"

        # --- Party-only battle stats ---
        level = 0
        hp = None
        max_hp = None
        stats = None

        if is_party and len(pkmn_data) >= _PARTY_POKEMON_SIZE:
            # Decrypt battle stats (84 bytes at 0x88-0xDB)
            encrypted_stats = pkmn_data[0x88 : 0x88 + _BATTLE_STATS_SIZE]
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
            # 0x05: Capsule (u8)
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
            ability=ability_label,
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
        self, main_block: bytes, game: str
    ) -> dict[str, list[Item]]:
        """Parse bag items from the main block.

        Returns empty pockets as a placeholder until exact offsets are
        confirmed with real save files.
        """
        pocket_names = [
            "Items", "Medicine", "Poke Balls", "TMs/HMs",
            "Berries", "Battle Items", "Key Items", "Free Space",
        ]
        return {name: [] for name in pocket_names}
