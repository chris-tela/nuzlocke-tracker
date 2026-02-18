"""Gen I save file parser (Red, Blue, Yellow).

Parses the binary save format used by Pokemon Red, Blue, and Yellow
for Game Boy. No encryption is used; just a single-byte checksum.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_I)
  - PKHeX.Core SAV1.cs
"""

from __future__ import annotations

import logging
import struct
import warnings

from pokesave.data.items import GEN1_ITEMS
from pokesave.data.moves import MOVE_NAMES
from pokesave.data.species import GEN1_INTERNAL_TO_NATIONAL, SPECIES_NAMES
from pokesave.encoding.gen1 import decode_string
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
# Constants -- International Red/Blue offsets
# ---------------------------------------------------------------------------

# Checksum range
_CHECKSUM_START = 0x2598
_CHECKSUM_END = 0x3522  # inclusive
_CHECKSUM_OFFSET = 0x3523

# Trainer data
_PLAYER_NAME_OFFSET = 0x2598
_PLAYER_NAME_LENGTH = 11
_TRAINER_ID_OFFSET = 0x2605
_MONEY_OFFSET = 0x25F3
_BADGES_OFFSET = 0x2602

# Playtime
_PLAYTIME_HOURS_OFFSET = 0x2CED
_PLAYTIME_MINUTES_OFFSET = 0x2CEF
_PLAYTIME_SECONDS_OFFSET = 0x2CF0

# Pokedex
_POKEDEX_OWNED_OFFSET = 0x25A3
_POKEDEX_SEEN_OFFSET = 0x25B6
_POKEDEX_BYTES = 19  # 19 bytes = 152 bits, covers 151 Pokemon

# Party
_PARTY_COUNT_OFFSET = 0x2F2C
_PARTY_SPECIES_OFFSET = 0x2F2D
_PARTY_DATA_OFFSET = 0x2F34
_PARTY_POKEMON_SIZE = 44
_BOX_POKEMON_SIZE = 33
_NAME_LENGTH = 11
_MAX_PARTY = 6

# Current box
_CURRENT_BOX_OFFSET = 0x30C0

# Bag items
_BAG_ITEMS_OFFSET = 0x25C9

# Badge names in bit order (bit 0 through bit 7)
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


class Gen1Parser(BaseParser):
    """Parser for Generation I save files (Red, Blue, Yellow)."""

    def parse(self, data: bytes) -> SaveFile:
        """Parse a Gen 1 save file into a structured SaveFile model."""
        # Validate checksum (warn but continue if invalid)
        if not self.validate_checksum(data):
            warnings.warn("Gen 1 checksum validation failed; data may be corrupt.")

        game = self.detect_version(data)
        japanese = self._is_japanese(data)

        trainer = self._parse_trainer(data, japanese)
        party = self._parse_party(data, japanese)
        boxes = self._parse_boxes(data, japanese)
        bag = self._parse_bag(data)

        return SaveFile(
            generation=1,
            game=game,
            trainer=trainer,
            party=party,
            boxes=boxes,
            bag=bag,
        )

    def validate_checksum(self, data: bytes) -> bool:
        """Validate the 8-bit complement checksum.

        Sum bytes from 0x2598 to 0x3522 (inclusive), complement, compare
        to the byte stored at 0x3523.
        """
        if len(data) <= _CHECKSUM_OFFSET:
            return False

        total = sum(data[_CHECKSUM_START : _CHECKSUM_END + 1])
        expected = (~total) & 0xFF
        stored = data[_CHECKSUM_OFFSET]
        return expected == stored

    def detect_version(self, data: bytes) -> str:
        """Detect whether this is Red/Blue or Yellow."""
        if self._is_yellow(data):
            return "Yellow"
        return "Red/Blue"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_japanese(data: bytes) -> bool:
        """Check if this is a Japanese save by testing list offsets.

        Japanese saves have party list at 0x2ED5 (not 0x2F2C).
        """
        jp_offset = 0x2ED5
        if jp_offset + 1 >= len(data):
            return False
        count = data[jp_offset]
        if count > 6:
            return False
        terminator_offset = jp_offset + 1 + count
        if terminator_offset >= len(data):
            return False
        return data[terminator_offset] == 0xFF

    @staticmethod
    def _is_yellow(data: bytes) -> bool:
        """Detect Yellow via starter byte at 0x29C3."""
        if len(data) <= 0x29C3:
            return False
        starter = data[0x29C3]
        if starter == 0x54:  # Pikachu internal index
            return True
        if starter == 0x00 and len(data) > 0x271C:
            return data[0x271C] != 0x00  # Pikachu friendship
        return False

    def _parse_trainer(self, data: bytes, japanese: bool) -> Trainer:
        """Parse trainer data from the save file."""
        name = decode_string(
            data[_PLAYER_NAME_OFFSET : _PLAYER_NAME_OFFSET + _PLAYER_NAME_LENGTH],
            japanese=japanese,
        )

        trainer_id = struct.unpack_from(">H", data, _TRAINER_ID_OFFSET)[0]

        money = _decode_bcd(data[_MONEY_OFFSET : _MONEY_OFFSET + 3])

        badges_byte = data[_BADGES_OFFSET]
        badges = [
            _KANTO_BADGES[i] for i in range(8) if badges_byte & (1 << i)
        ]

        hours = struct.unpack_from("<H", data, _PLAYTIME_HOURS_OFFSET)[0]
        minutes = data[_PLAYTIME_MINUTES_OFFSET]
        seconds = data[_PLAYTIME_SECONDS_OFFSET]
        playtime = Playtime(hours=hours, minutes=minutes, seconds=seconds)

        pokedex_owned = _count_bits(
            data[_POKEDEX_OWNED_OFFSET : _POKEDEX_OWNED_OFFSET + _POKEDEX_BYTES]
        )
        pokedex_seen = _count_bits(
            data[_POKEDEX_SEEN_OFFSET : _POKEDEX_SEEN_OFFSET + _POKEDEX_BYTES]
        )

        return Trainer(
            name=name,
            id=trainer_id,
            secret_id=None,
            gender=None,
            money=money,
            badges=badges,
            playtime=playtime,
            pokedex_owned=pokedex_owned,
            pokedex_seen=pokedex_seen,
        )

    def _parse_party(self, data: bytes, japanese: bool) -> list[Pokemon]:
        """Parse the party Pokemon list."""
        count = data[_PARTY_COUNT_OFFSET]
        if count > _MAX_PARTY:
            count = _MAX_PARTY

        pokemon_list: list[Pokemon] = []

        # OT names start after all 6 pokemon data slots (always 6 slots reserved)
        ot_names_start = _PARTY_DATA_OFFSET + _MAX_PARTY * _PARTY_POKEMON_SIZE
        # Nicknames start after OT names (6 slots of 11 bytes each)
        nicknames_start = ot_names_start + _MAX_PARTY * _NAME_LENGTH

        for i in range(count):
            # Check species byte in the species list
            species_list_byte = data[_PARTY_SPECIES_OFFSET + i]
            if species_list_byte == 0x00 or species_list_byte == 0xFF:
                continue

            pkmn_offset = _PARTY_DATA_OFFSET + i * _PARTY_POKEMON_SIZE
            pkmn_data = data[pkmn_offset : pkmn_offset + _PARTY_POKEMON_SIZE]

            if len(pkmn_data) < _PARTY_POKEMON_SIZE:
                continue

            ot_name_offset = ot_names_start + i * _NAME_LENGTH
            ot_name = decode_string(
                data[ot_name_offset : ot_name_offset + _NAME_LENGTH],
                japanese=japanese,
            )

            nick_offset = nicknames_start + i * _NAME_LENGTH
            nickname = decode_string(
                data[nick_offset : nick_offset + _NAME_LENGTH],
                japanese=japanese,
            )

            try:
                pkmn = _parse_party_pokemon(pkmn_data, ot_name, nickname, "party")
                if pkmn is not None:
                    pokemon_list.append(pkmn)
            except Exception:
                logger.warning("Failed to parse party Pokemon at slot %d", i)

        return pokemon_list

    def _parse_boxes(self, data: bytes, japanese: bool) -> dict[str, list[Pokemon]]:
        """Parse PC box Pokemon.

        For the initial implementation, we parse only the current box
        (stored in main RAM at 0x30C0). Other boxes are in SRAM banks
        and require bank-switching logic that is complex to replicate.
        """
        boxes: dict[str, list[Pokemon]] = {}

        # Parse current box
        current_box = self._parse_single_box(
            data, _CURRENT_BOX_OFFSET, japanese, "Current Box"
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
    ) -> list[Pokemon]:
        """Parse a single PC box at the given offset.

        Box structure:
        - 1 byte: count
        - count+1 bytes: species list (terminated by 0xFF)
        - 20 * 33 bytes: Pokemon data (33 bytes each for box pokemon)
        - 20 * 11 bytes: OT names
        - 20 * 11 bytes: Nicknames
        """
        max_box = 20

        if offset >= len(data):
            return []

        count = data[offset]
        if count > max_box:
            count = max_box

        species_list_offset = offset + 1
        # Pokemon data starts after species list + terminator (max_box + 1 bytes)
        pkmn_data_offset = species_list_offset + max_box + 1
        ot_names_offset = pkmn_data_offset + max_box * _BOX_POKEMON_SIZE
        nicknames_offset = ot_names_offset + max_box * _NAME_LENGTH

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
                pkmn = _parse_box_pokemon(pkmn_data, ot_name, nickname, box_name)
                if pkmn is not None:
                    pokemon_list.append(pkmn)
            except Exception:
                logger.warning("Failed to parse box Pokemon at slot %d in %s", i, box_name)

        return pokemon_list

    def _parse_bag(self, data: bytes) -> dict[str, list[Item]]:
        """Parse bag items.

        Gen 1 has a single bag pocket. Format:
        - 1 byte: item count
        - N pairs of (item_id, quantity)
        - Terminated by 0xFF
        """
        items: list[Item] = []
        offset = _BAG_ITEMS_OFFSET

        if offset >= len(data):
            return {"Items": items}

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

            item_name = GEN1_ITEMS.get(item_id, f"Unknown ({item_id:#04x})")
            items.append(Item(name=item_name, quantity=quantity))

        return {"Items": items}


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------


def _decode_bcd(data: bytes) -> int:
    """Decode BCD (Binary Coded Decimal) bytes to an integer.

    Each nibble represents a decimal digit. For example:
    bytes 0x01, 0x23, 0x45 -> 12345.
    """
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


def _resolve_species(internal_index: int) -> tuple[int, str]:
    """Convert Gen 1 internal species index to (national_dex, name).

    Returns (0, "MissingNo.") if the index is not recognized.
    """
    national = GEN1_INTERNAL_TO_NATIONAL.get(internal_index)
    if national is None:
        return (0, "MissingNo.")
    name = SPECIES_NAMES.get(national, f"Unknown #{national}")
    return (national, name)


def _is_shiny_gen1(atk_dv: int, def_dv: int, spd_dv: int, spc_dv: int) -> bool:
    """Determine if a Gen 1 Pokemon would be shiny when traded to Gen 2.

    Shiny criteria: Defense DV=10, Speed DV=10, Special DV=10,
    Attack DV in {2, 3, 6, 7, 10, 11, 14, 15}.
    """
    if def_dv != 10 or spd_dv != 10 or spc_dv != 10:
        return False
    return atk_dv in {2, 3, 6, 7, 10, 11, 14, 15}


def _parse_party_pokemon(
    data: bytes,
    ot_name: str,
    nickname: str,
    location: str,
) -> Pokemon | None:
    """Parse a 44-byte party Pokemon structure.

    All multi-byte values in Gen 1 are big-endian.
    """
    if len(data) < _PARTY_POKEMON_SIZE:
        return None

    internal_species = data[0x00]
    if internal_species == 0x00:
        return None

    species_id, species_name = _resolve_species(internal_species)

    current_hp = struct.unpack_from(">H", data, 0x01)[0]
    level_box = data[0x03]

    # Moves
    move_ids = [data[0x08], data[0x09], data[0x0A], data[0x0B]]

    # OT ID
    ot_id = struct.unpack_from(">H", data, 0x0C)[0]

    # Stat Experience (EVs in Gen 1-2 terminology)
    hp_ev = struct.unpack_from(">H", data, 0x11)[0]
    atk_ev = struct.unpack_from(">H", data, 0x13)[0]
    def_ev = struct.unpack_from(">H", data, 0x15)[0]
    spd_ev = struct.unpack_from(">H", data, 0x17)[0]
    spc_ev = struct.unpack_from(">H", data, 0x19)[0]

    # DVs (IVs in Gen 1-2 terminology)
    atk_dv = (data[0x1B] >> 4) & 0x0F
    def_dv = data[0x1B] & 0x0F
    spd_dv = (data[0x1C] >> 4) & 0x0F
    spc_dv = data[0x1C] & 0x0F
    # HP DV is derived from the low bit of each other DV
    hp_dv = (
        ((atk_dv & 1) << 3)
        | ((def_dv & 1) << 2)
        | ((spd_dv & 1) << 1)
        | (spc_dv & 1)
    )

    # PP for moves 1-4
    pp_values = []
    for j in range(4):
        pp_byte = data[0x1D + j]
        current_pp = pp_byte & 0x3F
        pp_ups = (pp_byte >> 6) & 0x03
        pp_values.append((current_pp, pp_ups))

    # Build Move list
    moves: list[Move] = []
    for j in range(4):
        move_id = move_ids[j]
        if move_id == 0:
            continue
        move_name = MOVE_NAMES.get(move_id, f"Move {move_id}")
        current_pp, pp_ups = pp_values[j]
        moves.append(Move(name=move_name, pp=current_pp, pp_max=None))

    # Party-only stats (bytes 0x21-0x2B)
    party_level = data[0x21]
    max_hp = struct.unpack_from(">H", data, 0x22)[0]
    attack = struct.unpack_from(">H", data, 0x24)[0]
    defense = struct.unpack_from(">H", data, 0x26)[0]
    speed = struct.unpack_from(">H", data, 0x28)[0]
    special = struct.unpack_from(">H", data, 0x2A)[0]

    # Use party level (recalculated) as the authoritative level
    level = party_level if party_level > 0 else level_box

    # Gen 1 has a single "Special" stat; map to both sp_attack and sp_defense
    stats = Stats(
        hp=max_hp,
        attack=attack,
        defense=defense,
        speed=speed,
        sp_attack=special,
        sp_defense=special,
    )

    # Gen 1 stat experience maps to both sp_attack and sp_defense EVs
    evs = EVs(
        hp=hp_ev,
        attack=atk_ev,
        defense=def_ev,
        speed=spd_ev,
        sp_attack=spc_ev,
        sp_defense=spc_ev,
    )

    # Gen 1 Special DV maps to both sp_attack and sp_defense IVs
    ivs = IVs(
        hp=hp_dv,
        attack=atk_dv,
        defense=def_dv,
        speed=spd_dv,
        sp_attack=spc_dv,
        sp_defense=spc_dv,
    )

    is_shiny = _is_shiny_gen1(atk_dv, def_dv, spd_dv, spc_dv)

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
        held_item=None,  # Gen 1 has no held items
        ability=None,  # Gen 1 has no abilities
        nature=None,  # Gen 1 has no natures
        friendship=None,  # Gen 1 has no friendship (except Yellow Pikachu)
        ot_name=ot_name,
        ot_id=ot_id,
        met_location=None,
        met_level=None,
        pokeball=None,
        pokerus=False,  # Gen 1 has no Pokerus
        is_shiny=is_shiny,
        is_egg=False,  # Gen 1 has no eggs
        location=location,
    )


def _parse_box_pokemon(
    data: bytes,
    ot_name: str,
    nickname: str,
    box_name: str,
) -> Pokemon | None:
    """Parse a 33-byte box Pokemon structure.

    Box Pokemon lack the party-only stats (bytes 0x21-0x2B of the party
    structure). The first 33 bytes are identical to the party structure.
    """
    if len(data) < _BOX_POKEMON_SIZE:
        return None

    internal_species = data[0x00]
    if internal_species == 0x00:
        return None

    species_id, species_name = _resolve_species(internal_species)

    level = data[0x03]

    # Moves
    move_ids = [data[0x08], data[0x09], data[0x0A], data[0x0B]]

    # OT ID
    ot_id = struct.unpack_from(">H", data, 0x0C)[0]

    # Stat Experience (EVs)
    hp_ev = struct.unpack_from(">H", data, 0x11)[0]
    atk_ev = struct.unpack_from(">H", data, 0x13)[0]
    def_ev = struct.unpack_from(">H", data, 0x15)[0]
    spd_ev = struct.unpack_from(">H", data, 0x17)[0]
    spc_ev = struct.unpack_from(">H", data, 0x19)[0]

    # DVs
    atk_dv = (data[0x1B] >> 4) & 0x0F
    def_dv = data[0x1B] & 0x0F
    spd_dv = (data[0x1C] >> 4) & 0x0F
    spc_dv = data[0x1C] & 0x0F
    hp_dv = (
        ((atk_dv & 1) << 3)
        | ((def_dv & 1) << 2)
        | ((spd_dv & 1) << 1)
        | (spc_dv & 1)
    )

    # PP
    pp_values = []
    for j in range(4):
        pp_byte = data[0x1D + j]
        current_pp = pp_byte & 0x3F
        pp_values.append(current_pp)

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

    is_shiny = _is_shiny_gen1(atk_dv, def_dv, spd_dv, spc_dv)

    return Pokemon(
        species=species_name,
        species_id=species_id,
        nickname=nickname if nickname else None,
        level=level,
        moves=moves,
        hp=None,  # Box Pokemon don't have current HP recalculated
        max_hp=None,
        stats=None,  # Box Pokemon don't have computed stats
        evs=evs,
        ivs=ivs,
        held_item=None,
        ability=None,
        nature=None,
        friendship=None,
        ot_name=ot_name,
        ot_id=ot_id,
        met_location=None,
        met_level=None,
        pokeball=None,
        pokerus=False,
        is_shiny=is_shiny,
        is_egg=False,
        location=box_name,
    )
