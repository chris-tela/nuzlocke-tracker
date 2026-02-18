"""Gen II save file parser (Gold, Silver, Crystal).

Parses the binary save format used by Pokemon Gold, Silver, and Crystal
for Game Boy Color. No encryption is used; two 16-bit checksums protect
data integrity.

Key differences from Gen 1:
  - 48-byte party Pokemon / 32-byte box Pokemon
  - Species index is National Dex number (no remapping needed)
  - Held items, friendship, Pokerus
  - Crystal adds caught data (met location/level/time of day/OT gender)
  - Multiple bag pockets
  - Johto + Kanto badges
  - Special stat split into Sp. Atk / Sp. Def for party stats

References:
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_II)
  - PKHeX.Core SAV2.cs
"""

from __future__ import annotations

import logging
import struct
import warnings

from pokesave.data.items import GEN2_ITEMS
from pokesave.data.moves import MOVE_NAMES
from pokesave.data.species import SPECIES_NAMES
from pokesave.encoding.gen1 import decode_string  # Gen 2 uses same encoding
from pokesave.models import (
    EVs,
    IVs,
    Item,
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
# Offsets per game variant (International only for v1)
# ---------------------------------------------------------------------------
# These are the offsets for Gold/Silver International saves.
# Crystal International uses slightly different offsets.

# We store offsets as dicts keyed by version string.

_OFFSETS: dict[str, dict[str, int]] = {
    "Gold/Silver": {
        "player_name": 0x200B,
        "trainer_id": 0x2009,
        "money": 0x23DB,
        "johto_badges": 0x23E5,
        "kanto_badges": 0x23E6,
        "playtime_hours": 0x2054,
        "playtime_minutes": 0x2056,
        "playtime_seconds": 0x2057,
        "party_count": 0x288A,
        "party_species": 0x288B,
        "party_data": 0x2892,
        "current_box": 0x2D6C,
        "pokedex_owned": 0x2A4C,
        "pokedex_seen": 0x2A6C,
        "items_pocket": 0x241A,
        "key_items_pocket": 0x2449,
        "balls_pocket": 0x2464,
        "tmhm_pocket": 0x247E,
        # Checksum 1 range
        "checksum1_start": 0x2009,
        "checksum1_end": 0x2D68,
        "checksum1_offset": 0x2D69,
    },
    "Crystal": {
        "player_name": 0x200B,
        "trainer_id": 0x2009,
        "money": 0x23DB,
        "johto_badges": 0x23E5,
        "kanto_badges": 0x23E6,
        "playtime_hours": 0x2054,
        "playtime_minutes": 0x2056,
        "playtime_seconds": 0x2057,
        "party_count": 0x2865,
        "party_species": 0x2866,
        "party_data": 0x286D,
        "current_box": 0x2D10,
        "pokedex_owned": 0x2A27,
        "pokedex_seen": 0x2A47,
        "items_pocket": 0x2420,
        "key_items_pocket": 0x244F,
        "balls_pocket": 0x2464,
        "tmhm_pocket": 0x247E,
        # Checksum 1 range
        "checksum1_start": 0x2009,
        "checksum1_end": 0x2B42,
        "checksum1_offset": 0x2D0D,
    },
}

# Name length in bytes (same as Gen 1)
_NAME_LENGTH = 11
_MAX_PARTY = 6

# Pokemon data sizes
_PARTY_POKEMON_SIZE = 48   # 48-byte core data for party
_PARTY_TOTAL_SIZE = 48     # Core data portion
_BOX_POKEMON_SIZE = 32     # 32-byte core data for box

# Party-only extra data (after core 48 bytes)
_PARTY_EXTRA_SIZE = 16     # Bytes 0x20-0x2F (status, HP, stats)

# PC Boxes
_MAX_BOX_POKEMON = 20

# Badge names
_JOHTO_BADGES = [
    "Zephyr",
    "Hive",
    "Plain",
    "Fog",
    "Storm",
    "Mineral",
    "Glacier",
    "Rising",
]

_KANTO_BADGES = [
    "Boulder",
    "Cascade",
    "Thunder",
    "Rainbow",
    "Soul",
    "Marsh",
    "Volcano",
    "Earth",
]

# Pokedex bytes (32 bytes covers 256 bits, we need 251)
_POKEDEX_BYTES = 32

# Crystal caught data: time of day names
_TIME_OF_DAY = {
    0: "Morning",
    1: "Day",
    2: "Night",
}


class Gen2Parser(BaseParser):
    """Parser for Generation II save files (Gold, Silver, Crystal)."""

    def parse(self, data: bytes) -> SaveFile:
        """Parse a Gen 2 save file into a structured SaveFile model."""
        game = self.detect_version(data)
        is_crystal = game == "Crystal"

        # Validate checksum (warn but continue if invalid)
        if not self.validate_checksum(data):
            warnings.warn("Gen 2 checksum validation failed; data may be corrupt.")

        offsets = _OFFSETS.get(game, _OFFSETS["Gold/Silver"])
        japanese = self._is_japanese(data, game)

        trainer = self._parse_trainer(data, offsets, japanese, is_crystal)
        party = self._parse_party(data, offsets, japanese, is_crystal)
        boxes = self._parse_boxes(data, offsets, japanese, is_crystal)
        bag = self._parse_bag(data, offsets)

        return SaveFile(
            generation=2,
            game=game,
            trainer=trainer,
            party=party,
            boxes=boxes,
            bag=bag,
        )

    def validate_checksum(self, data: bytes) -> bool:
        """Validate the primary 16-bit checksum.

        Checksum 1 is the sum of bytes in the main data range,
        stored as a 16-bit little-endian value.
        """
        game = self.detect_version(data)
        offsets = _OFFSETS.get(game, _OFFSETS["Gold/Silver"])

        start = offsets["checksum1_start"]
        end = offsets["checksum1_end"]
        cksum_offset = offsets["checksum1_offset"]

        if cksum_offset + 2 > len(data):
            return False

        total = sum(data[start : end + 1]) & 0xFFFF
        stored = struct.unpack_from("<H", data, cksum_offset)[0]

        return total == stored

    def detect_version(self, data: bytes) -> str:
        """Detect Gold/Silver vs Crystal.

        Uses the party list validation approach: check which set of
        offsets produces a valid Pokemon list structure.
        """
        # Crystal international
        if self._has_valid_list(data, 0x2865, _MAX_PARTY):
            return "Crystal"
        # Gold/Silver international (default)
        return "Gold/Silver"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_japanese(data: bytes, game: str) -> bool:
        """Check if this is a Japanese save.

        Japanese Gen 2 saves are 64 KiB (0x10000 bytes).
        International saves are 32 KiB (0x8000 bytes).
        """
        return len(data) == 0x10000

    @staticmethod
    def _has_valid_list(data: bytes, offset: int, max_count: int) -> bool:
        """Check if offset contains a valid Gen 2 Pokemon list."""
        if offset >= len(data):
            return False
        count = data[offset]
        if count > max_count:
            return False
        terminator_offset = offset + 1 + count
        if terminator_offset >= len(data):
            return False
        return data[terminator_offset] == 0xFF

    def _parse_trainer(
        self,
        data: bytes,
        offsets: dict[str, int],
        japanese: bool,
        is_crystal: bool,
    ) -> Trainer:
        """Parse trainer data from the save file."""
        name_off = offsets["player_name"]
        name = decode_string(
            data[name_off : name_off + _NAME_LENGTH],
            japanese=japanese,
        )

        trainer_id = struct.unpack_from(">H", data, offsets["trainer_id"])[0]

        money = _decode_bcd(data[offsets["money"] : offsets["money"] + 3])

        # Johto badges
        johto_byte = data[offsets["johto_badges"]]
        badges = [
            _JOHTO_BADGES[i] for i in range(8) if johto_byte & (1 << i)
        ]

        # Kanto badges
        kanto_byte = data[offsets["kanto_badges"]]
        badges.extend(
            _KANTO_BADGES[i] for i in range(8) if kanto_byte & (1 << i)
        )

        hours = struct.unpack_from("<H", data, offsets["playtime_hours"])[0]
        minutes = data[offsets["playtime_minutes"]]
        seconds = data[offsets["playtime_seconds"]]
        playtime = Playtime(hours=hours, minutes=minutes, seconds=seconds)

        # Pokedex
        owned_off = offsets["pokedex_owned"]
        seen_off = offsets["pokedex_seen"]
        pokedex_owned = _count_bits(data[owned_off : owned_off + _POKEDEX_BYTES])
        pokedex_seen = _count_bits(data[seen_off : seen_off + _POKEDEX_BYTES])

        # Gender is Crystal-only (stored in trainer data)
        gender = None
        if is_crystal:
            # Crystal stores gender at player_name offset - 1 (0x200A)
            # Actually stored at 0x3E3D in Crystal INT -- but this is less
            # reliable. For simplicity we leave gender as None unless we can
            # verify the offset.
            pass

        return Trainer(
            name=name,
            id=trainer_id,
            secret_id=None,
            gender=gender,
            money=money,
            badges=badges,
            playtime=playtime,
            pokedex_owned=pokedex_owned,
            pokedex_seen=pokedex_seen,
        )

    def _parse_party(
        self,
        data: bytes,
        offsets: dict[str, int],
        japanese: bool,
        is_crystal: bool,
    ) -> list[Pokemon]:
        """Parse the party Pokemon list."""
        count_offset = offsets["party_count"]
        count = data[count_offset]
        if count > _MAX_PARTY:
            count = _MAX_PARTY

        species_offset = offsets["party_species"]
        data_offset = offsets["party_data"]

        # Each party pokemon: 48 bytes core + 16 bytes party-only = 64 bytes total
        party_entry_size = _PARTY_POKEMON_SIZE + _PARTY_EXTRA_SIZE

        # OT names start after all 6 party pokemon data slots
        ot_names_start = data_offset + _MAX_PARTY * party_entry_size
        # Nicknames after OT names
        nicknames_start = ot_names_start + _MAX_PARTY * _NAME_LENGTH

        pokemon_list: list[Pokemon] = []

        for i in range(count):
            species_byte = data[species_offset + i]
            if species_byte == 0x00 or species_byte == 0xFF:
                continue

            entry_offset = data_offset + i * party_entry_size
            pkmn_data = data[entry_offset : entry_offset + party_entry_size]

            if len(pkmn_data) < party_entry_size:
                continue

            ot_name_off = ot_names_start + i * _NAME_LENGTH
            ot_name = decode_string(
                data[ot_name_off : ot_name_off + _NAME_LENGTH],
                japanese=japanese,
            )

            nick_off = nicknames_start + i * _NAME_LENGTH
            nickname = decode_string(
                data[nick_off : nick_off + _NAME_LENGTH],
                japanese=japanese,
            )

            try:
                pkmn = _parse_party_pokemon(
                    pkmn_data, ot_name, nickname, "party", is_crystal
                )
                if pkmn is not None:
                    pokemon_list.append(pkmn)
            except Exception:
                logger.warning("Failed to parse party Pokemon at slot %d", i)

        return pokemon_list

    def _parse_boxes(
        self,
        data: bytes,
        offsets: dict[str, int],
        japanese: bool,
        is_crystal: bool,
    ) -> dict[str, list[Pokemon]]:
        """Parse PC box Pokemon.

        Like Gen 1, the current box is in main RAM. Other boxes are in
        SRAM banks. We parse only the current box for now.
        """
        boxes: dict[str, list[Pokemon]] = {}

        current_box_offset = offsets["current_box"]
        current_box = self._parse_single_box(
            data, current_box_offset, japanese, "Current Box", is_crystal
        )
        if current_box:
            boxes["Current Box"] = current_box

        return boxes

    def _parse_single_box(
        self,
        data: bytes,
        offset: int,
        japanese: bool,
        box_name: str,
        is_crystal: bool,
    ) -> list[Pokemon]:
        """Parse a single PC box.

        Box structure:
        - 1 byte: count
        - count+1 bytes: species list (terminated by 0xFF)
        - 20 * 32 bytes: Pokemon data
        - 20 * 11 bytes: OT names
        - 20 * 11 bytes: Nicknames
        """
        if offset >= len(data):
            return []

        count = data[offset]
        if count > _MAX_BOX_POKEMON:
            count = _MAX_BOX_POKEMON

        species_list_offset = offset + 1
        pkmn_data_offset = species_list_offset + _MAX_BOX_POKEMON + 1
        ot_names_offset = pkmn_data_offset + _MAX_BOX_POKEMON * _BOX_POKEMON_SIZE
        nicknames_offset = ot_names_offset + _MAX_BOX_POKEMON * _NAME_LENGTH

        pokemon_list: list[Pokemon] = []

        for i in range(count):
            species_byte = data[species_list_offset + i]
            if species_byte == 0x00 or species_byte == 0xFF:
                continue

            entry_offset = pkmn_data_offset + i * _BOX_POKEMON_SIZE
            pkmn_data = data[entry_offset : entry_offset + _BOX_POKEMON_SIZE]

            if len(pkmn_data) < _BOX_POKEMON_SIZE:
                continue

            ot_name_off = ot_names_offset + i * _NAME_LENGTH
            ot_name = decode_string(
                data[ot_name_off : ot_name_off + _NAME_LENGTH],
                japanese=japanese,
            )

            nick_off = nicknames_offset + i * _NAME_LENGTH
            nickname = decode_string(
                data[nick_off : nick_off + _NAME_LENGTH],
                japanese=japanese,
            )

            try:
                pkmn = _parse_box_pokemon(
                    pkmn_data, ot_name, nickname, box_name, is_crystal
                )
                if pkmn is not None:
                    pokemon_list.append(pkmn)
            except Exception:
                logger.warning(
                    "Failed to parse box Pokemon at slot %d in %s", i, box_name
                )

        return pokemon_list

    def _parse_bag(
        self, data: bytes, offsets: dict[str, int]
    ) -> dict[str, list[Item]]:
        """Parse bag items from multiple pockets.

        Gen 2 has four pockets: Items, Key Items, Balls, TM/HM.
        Each pocket has a count byte followed by (item_id, quantity) pairs.
        """
        bag: dict[str, list[Item]] = {}

        bag["Items"] = _parse_item_pocket(data, offsets["items_pocket"])
        bag["Key Items"] = _parse_item_pocket(data, offsets["key_items_pocket"])
        bag["Balls"] = _parse_item_pocket(data, offsets["balls_pocket"])
        bag["TM/HM"] = _parse_item_pocket(data, offsets["tmhm_pocket"])

        return bag


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------


def _decode_bcd(data: bytes) -> int:
    """Decode BCD (Binary Coded Decimal) bytes to an integer."""
    result = 0
    for byte in data:
        high = (byte >> 4) & 0x0F
        low = byte & 0x0F
        result = result * 100 + high * 10 + low
    return result


def _count_bits(data: bytes) -> int:
    """Count the number of set bits in a byte sequence."""
    count = 0
    for byte in data:
        count += bin(byte).count("1")
    return count


def _resolve_species(species_id: int) -> tuple[int, str]:
    """Look up species name by National Dex number.

    Gen 2 uses National Dex numbers directly (no remapping needed).
    Returns (species_id, name).
    """
    if species_id == 0 or species_id > 251:
        return (0, f"Unknown #{species_id}")
    name = SPECIES_NAMES.get(species_id, f"Unknown #{species_id}")
    return (species_id, name)


def _is_shiny_gen2(atk_dv: int, def_dv: int, spd_dv: int, spc_dv: int) -> bool:
    """Determine if a Gen 2 Pokemon is shiny based on DVs.

    Shiny criteria: Defense DV=10, Speed DV=10, Special DV=10,
    Attack DV in {2, 3, 6, 7, 10, 11, 14, 15}.
    """
    if def_dv != 10 or spd_dv != 10 or spc_dv != 10:
        return False
    return atk_dv in {2, 3, 6, 7, 10, 11, 14, 15}


def _parse_caught_data(caught_word: int) -> dict:
    """Parse Crystal's 2-byte caught data field.

    Bit layout (16 bits total):
    - Bits 15-14: time of day (0=morning, 1=day, 2=night)
    - Bits 13-8:  level caught (0-63)
    - Bits 7-1:   location index (0-127)
    - Bit 0:      OT gender (0=male, 1=female)
    """
    time_of_day_code = (caught_word >> 14) & 0x03
    level_caught = (caught_word >> 8) & 0x3F
    location_index = (caught_word >> 1) & 0x7F
    ot_gender_bit = caught_word & 0x01

    return {
        "time_of_day": _TIME_OF_DAY.get(time_of_day_code, "Unknown"),
        "level_caught": level_caught,
        "location_index": location_index,
        "ot_gender": "Female" if ot_gender_bit else "Male",
    }


def _parse_item_pocket(data: bytes, offset: int) -> list[Item]:
    """Parse a single bag pocket.

    Format: count byte, then pairs of (item_id, quantity), terminated by 0xFF.
    """
    items: list[Item] = []

    if offset >= len(data):
        return items

    count = data[offset]
    offset += 1

    for _ in range(count):
        if offset + 1 >= len(data):
            break

        item_id = data[offset]
        quantity = data[offset + 1]
        offset += 2

        if item_id == 0xFF:
            break
        if item_id == 0x00:
            continue

        item_name = GEN2_ITEMS.get(item_id, f"Unknown ({item_id:#04x})")
        items.append(Item(name=item_name, quantity=quantity))

    return items


def _parse_party_pokemon(
    data: bytes,
    ot_name: str,
    nickname: str,
    location: str,
    is_crystal: bool,
) -> Pokemon | None:
    """Parse a 64-byte party Pokemon (48 core + 16 party-only).

    48-byte core structure (big-endian for multi-byte values):
    - 0x00: species (1 byte, National Dex number)
    - 0x01: held item
    - 0x02-0x05: moves 1-4
    - 0x06-0x07: OT ID (2 bytes big-endian)
    - 0x08-0x0A: experience (3 bytes big-endian)
    - 0x0B-0x14: stat experience (5 values, 2 bytes each)
    - 0x15: Attack DV (upper 4) / Defense DV (lower 4)
    - 0x16: Speed DV (upper 4) / Special DV (lower 4)
    - 0x17-0x1A: PP for moves 1-4
    - 0x1B: Friendship
    - 0x1C: Pokerus
    - 0x1D-0x1E: Caught data (Crystal only)
    - 0x1F: Level

    Party-only (0x20-0x2F):
    - 0x20: status condition
    - 0x21: unused
    - 0x22-0x23: current HP
    - 0x24-0x25: max HP
    - 0x26-0x27: attack
    - 0x28-0x29: defense
    - 0x2A-0x2B: speed
    - 0x2C-0x2D: sp.atk
    - 0x2E-0x2F: sp.def
    """
    total_size = _PARTY_POKEMON_SIZE + _PARTY_EXTRA_SIZE
    if len(data) < total_size:
        return None

    species_id = data[0x00]
    if species_id == 0x00 or species_id == 0xFF:
        return None

    species_id, species_name = _resolve_species(species_id)
    if species_id == 0:
        return None

    # Held item
    held_item_id = data[0x01]
    held_item = None
    if held_item_id != 0x00:
        held_item = GEN2_ITEMS.get(held_item_id, f"Unknown ({held_item_id:#04x})")

    # Moves
    move_ids = [data[0x02], data[0x03], data[0x04], data[0x05]]

    # OT ID
    ot_id = struct.unpack_from(">H", data, 0x06)[0]

    # Stat Experience (EVs in Gen 1-2 terminology)
    hp_ev = struct.unpack_from(">H", data, 0x0B)[0]
    atk_ev = struct.unpack_from(">H", data, 0x0D)[0]
    def_ev = struct.unpack_from(">H", data, 0x0F)[0]
    spd_ev = struct.unpack_from(">H", data, 0x11)[0]
    spc_ev = struct.unpack_from(">H", data, 0x13)[0]

    # DVs
    atk_dv = (data[0x15] >> 4) & 0x0F
    def_dv = data[0x15] & 0x0F
    spd_dv = (data[0x16] >> 4) & 0x0F
    spc_dv = data[0x16] & 0x0F
    hp_dv = (
        ((atk_dv & 1) << 3)
        | ((def_dv & 1) << 2)
        | ((spd_dv & 1) << 1)
        | (spc_dv & 1)
    )

    # PP for moves 1-4
    pp_values = []
    for j in range(4):
        pp_byte = data[0x17 + j]
        current_pp = pp_byte & 0x3F
        pp_ups = (pp_byte >> 6) & 0x03
        pp_values.append((current_pp, pp_ups))

    # Friendship
    friendship = data[0x1B]

    # Pokerus
    pokerus_byte = data[0x1C]
    has_pokerus = pokerus_byte != 0

    # Caught data (Crystal only)
    met_location = None
    met_level = None
    if is_crystal:
        caught_word = struct.unpack_from(">H", data, 0x1D)[0]
        if caught_word != 0:
            caught = _parse_caught_data(caught_word)
            met_level = caught["level_caught"]
            met_location = f"Location {caught['location_index']}"

    # Level (from core data)
    level = data[0x1F]

    # Build Move list
    moves: list[Move] = []
    for j in range(4):
        move_id = move_ids[j]
        if move_id == 0:
            continue
        move_name = MOVE_NAMES.get(move_id, f"Move {move_id}")
        current_pp, pp_ups = pp_values[j]
        moves.append(Move(name=move_name, pp=current_pp, pp_max=None))

    # Party-only stats
    current_hp = struct.unpack_from(">H", data, 0x22)[0]
    max_hp = struct.unpack_from(">H", data, 0x24)[0]
    attack = struct.unpack_from(">H", data, 0x26)[0]
    defense = struct.unpack_from(">H", data, 0x28)[0]
    speed = struct.unpack_from(">H", data, 0x2A)[0]
    sp_attack = struct.unpack_from(">H", data, 0x2C)[0]
    sp_defense = struct.unpack_from(">H", data, 0x2E)[0]

    stats = Stats(
        hp=max_hp,
        attack=attack,
        defense=defense,
        speed=speed,
        sp_attack=sp_attack,
        sp_defense=sp_defense,
    )

    # Gen 2 stat experience: Special stat exp maps to both sp_atk and sp_def
    evs = EVs(
        hp=hp_ev,
        attack=atk_ev,
        defense=def_ev,
        speed=spd_ev,
        sp_attack=spc_ev,
        sp_defense=spc_ev,
    )

    # Gen 2 Special DV maps to both sp_atk and sp_def IVs
    ivs = IVs(
        hp=hp_dv,
        attack=atk_dv,
        defense=def_dv,
        speed=spd_dv,
        sp_attack=spc_dv,
        sp_defense=spc_dv,
    )

    is_shiny = _is_shiny_gen2(atk_dv, def_dv, spd_dv, spc_dv)

    return Pokemon(
        species=species_name,
        species_id=species_id,
        nickname=nickname if nickname else None,
        level=level,
        moves=moves,
        hp=current_hp,
        max_hp=max_hp,
        stats=stats,
        evs=evs,
        ivs=ivs,
        held_item=held_item,
        ability=None,  # Gen 2 has no abilities
        nature=None,  # Gen 2 has no natures
        friendship=friendship,
        ot_name=ot_name,
        ot_id=ot_id,
        met_location=met_location,
        met_level=met_level,
        pokeball=None,  # Gen 2 doesn't store pokeball type
        pokerus=has_pokerus,
        is_shiny=is_shiny,
        is_egg=False,  # Egg detection would need species 0xFD check
        location=location,
    )


def _parse_box_pokemon(
    data: bytes,
    ot_name: str,
    nickname: str,
    box_name: str,
    is_crystal: bool,
) -> Pokemon | None:
    """Parse a 32-byte box Pokemon structure.

    Same as the first 32 bytes of the party structure (no party-only stats).
    Note: the 48-byte core structure stops at 0x1F (level) for party pokemon;
    box pokemon are only the first 32 bytes (0x00-0x1F).
    """
    if len(data) < _BOX_POKEMON_SIZE:
        return None

    species_id = data[0x00]
    if species_id == 0x00 or species_id == 0xFF:
        return None

    species_id, species_name = _resolve_species(species_id)
    if species_id == 0:
        return None

    # Held item
    held_item_id = data[0x01]
    held_item = None
    if held_item_id != 0x00:
        held_item = GEN2_ITEMS.get(held_item_id, f"Unknown ({held_item_id:#04x})")

    # Moves
    move_ids = [data[0x02], data[0x03], data[0x04], data[0x05]]

    # OT ID
    ot_id = struct.unpack_from(">H", data, 0x06)[0]

    # Stat Experience (EVs)
    hp_ev = struct.unpack_from(">H", data, 0x0B)[0]
    atk_ev = struct.unpack_from(">H", data, 0x0D)[0]
    def_ev = struct.unpack_from(">H", data, 0x0F)[0]
    spd_ev = struct.unpack_from(">H", data, 0x11)[0]
    spc_ev = struct.unpack_from(">H", data, 0x13)[0]

    # DVs
    atk_dv = (data[0x15] >> 4) & 0x0F
    def_dv = data[0x15] & 0x0F
    spd_dv = (data[0x16] >> 4) & 0x0F
    spc_dv = data[0x16] & 0x0F
    hp_dv = (
        ((atk_dv & 1) << 3)
        | ((def_dv & 1) << 2)
        | ((spd_dv & 1) << 1)
        | (spc_dv & 1)
    )

    # PP
    pp_values = []
    for j in range(4):
        pp_byte = data[0x17 + j]
        current_pp = pp_byte & 0x3F
        pp_values.append(current_pp)

    # Friendship
    friendship = data[0x1B]

    # Pokerus
    pokerus_byte = data[0x1C]
    has_pokerus = pokerus_byte != 0

    # Caught data (Crystal only)
    met_location = None
    met_level = None
    if is_crystal:
        caught_word = struct.unpack_from(">H", data, 0x1D)[0]
        if caught_word != 0:
            caught = _parse_caught_data(caught_word)
            met_level = caught["level_caught"]
            met_location = f"Location {caught['location_index']}"

    # Level
    level = data[0x1F]

    # Build Move list
    moves: list[Move] = []
    for j in range(4):
        move_id = move_ids[j]
        if move_id == 0:
            continue
        move_name = MOVE_NAMES.get(move_id, f"Move {move_id}")
        moves.append(Move(name=move_name, pp=pp_values[j], pp_max=None))

    evs = EVs(
        hp=hp_ev,
        attack=atk_ev,
        defense=def_ev,
        speed=spd_ev,
        sp_attack=spc_ev,
        sp_defense=spc_ev,
    )

    ivs = IVs(
        hp=hp_dv,
        attack=atk_dv,
        defense=def_dv,
        speed=spd_dv,
        sp_attack=spc_dv,
        sp_defense=spc_dv,
    )

    is_shiny = _is_shiny_gen2(atk_dv, def_dv, spd_dv, spc_dv)

    return Pokemon(
        species=species_name,
        species_id=species_id,
        nickname=nickname if nickname else None,
        level=level,
        moves=moves,
        hp=None,
        max_hp=None,
        stats=None,
        evs=evs,
        ivs=ivs,
        held_item=held_item,
        ability=None,
        nature=None,
        friendship=friendship,
        ot_name=ot_name,
        ot_id=ot_id,
        met_location=met_location,
        met_level=met_level,
        pokeball=None,
        pokerus=has_pokerus,
        is_shiny=is_shiny,
        is_egg=False,
        location=box_name,
    )
