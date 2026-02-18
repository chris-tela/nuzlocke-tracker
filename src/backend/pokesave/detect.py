"""Auto-detect save file generation and game version.

Algorithm sourced from PKHeX's SaveUtil.cs. Detection uses file size as
a gatekeeper, then structural validation to disambiguate candidates
within the same size class.
"""

from __future__ import annotations

import struct

# ---------------------------------------------------------------------------
# File size constants (bytes)
# ---------------------------------------------------------------------------

SIZE_G1RAW = 0x8000        # 32 KiB -- also Gen 2 international
SIZE_G2RAW_J = 0x10000     # 64 KiB -- Gen 2 Japanese only
SIZE_G3RAW = 0x20000       # 128 KiB
SIZE_G3RAWHALF = 0x10000   # 64 KiB -- Gen 3 half-size (single save slot)
SIZE_G4RAW = 0x80000       # 512 KiB -- also Gen 5

# Known emulator footer sizes (appended after the real save data)
_FOOTER_RTC = 0x2C         # 44 bytes -- RTC data (Crystal, some Gen 3)
_FOOTER_POKEMON_STADIUM = 0x10  # 16 bytes -- DeSmuME / Stadium footer

# Gen 4 GeneralSize per game (used in footer validation)
_G4_DP_GENERAL_SIZE = 0xC100
_G4_PT_GENERAL_SIZE = 0xCF2C
_G4_HGSS_GENERAL_SIZE = 0xF628

# Gen 5 main sizes and info lengths
_G5_BW_MAIN_SIZE = 0x24000
_G5_BW_INFO_LENGTH = 0x8C
_G5_B2W2_MAIN_SIZE = 0x26000
_G5_B2W2_INFO_LENGTH = 0x94

# Gen 3 sector size
_G3_SECTOR_SIZE = 0x1000  # 4 KiB per sector


def detect(data: bytes) -> tuple[int, str]:
    """Detect the generation and game version of a save file.

    Handles emulator footers (RTC, DeSmuME) by trying trimmed sizes
    when the raw size doesn't match a known format.

    Args:
        data: Raw bytes of the save file.

    Returns:
        Tuple of (generation, game_version_string).

    Raises:
        ValueError: If the file cannot be identified as a known save format.
    """
    length = len(data)

    # Try exact size match first, then trimmed sizes for emulator footers.
    trimmed = _trim_emulator_footer(data)

    if len(trimmed) == SIZE_G1RAW:
        # Could be Gen 1 or Gen 2 (international)
        result = _try_g1(trimmed)
        if result is not None:
            return result
        result = _try_g2(trimmed)
        if result is not None:
            return result
        raise ValueError(
            f"File is {length} bytes (32 KiB base) but does not match Gen 1 or Gen 2 structure."
        )

    if len(trimmed) == SIZE_G2RAW_J:
        # Could be Gen 2 Japanese or Gen 3 half-size
        result = _try_g2_japanese(trimmed)
        if result is not None:
            return result
        # Half-size Gen 3 save (single slot only)
        result = _try_g3(trimmed)
        if result is not None:
            return result
        raise ValueError(
            f"File is {length} bytes (64 KiB base) but does not match Gen 2 Japanese or Gen 3 half-size structure."
        )

    if len(trimmed) == SIZE_G3RAW:
        result = _try_g3(trimmed)
        if result is not None:
            return result
        raise ValueError(
            f"File is {length} bytes (128 KiB base) but does not match Gen 3 structure."
        )

    if len(trimmed) == SIZE_G4RAW:
        # Could be Gen 4 or Gen 5
        result = _try_g4(trimmed)
        if result is not None:
            return result
        result = _try_g5(trimmed)
        if result is not None:
            return result
        raise ValueError(
            f"File is {length} bytes (512 KiB base) but does not match Gen 4 or Gen 5 structure."
        )

    expected = [
        f"  32 KiB (0x{SIZE_G1RAW:X}) -- Gen 1 / Gen 2",
        f"  64 KiB (0x{SIZE_G2RAW_J:X}) -- Gen 2 Japanese / Gen 3 half-size",
        f" 128 KiB (0x{SIZE_G3RAW:X}) -- Gen 3",
        f" 512 KiB (0x{SIZE_G4RAW:X}) -- Gen 4 / Gen 5",
    ]
    raise ValueError(
        f"Unrecognized file size: {length} bytes (0x{length:X}).\n"
        f"Expected one of:\n" + "\n".join(expected)
    )


def _trim_emulator_footer(data: bytes) -> bytes:
    """Strip known emulator footer bytes to get the base save data.

    Emulators often append extra data after the real save:
    - RTC footer: 44 bytes (0x2C) -- common with Gen 2 Crystal
    - DeSmuME/Stadium: 16 bytes (0x10) -- common with Gen 3/4
    - Battery-backed SRAM padding: 122 bytes, 128 bytes

    We check if (length - footer_size) matches a known save size.
    """
    length = len(data)
    known_sizes = {SIZE_G1RAW, SIZE_G2RAW_J, SIZE_G3RAW, SIZE_G3RAWHALF, SIZE_G4RAW}
    footer_sizes = [_FOOTER_RTC, _FOOTER_POKEMON_STADIUM, 0x7A, 0x80]

    # If already a known size, no trimming needed
    if length in known_sizes:
        return data

    # Try each known footer size
    for footer in footer_sizes:
        base = length - footer
        if base in known_sizes:
            return data[:base]

    # No known footer matched -- return as-is (will fail size check)
    return data


# ---------------------------------------------------------------------------
# Gen 1 detection
# ---------------------------------------------------------------------------

def _try_g1(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 1 save file."""
    if _is_g1_international(data):
        version = _detect_yellow_or_rb(data)
        return (1, version)
    if _is_g1_japanese(data):
        version = _detect_yellow_or_rb(data)
        return (1, version)
    return None


def _is_g1_international(data: bytes) -> bool:
    """Check Gen 1 international list structures."""
    return (
        _has_list_at(data, 0x2F2C, 0x30C0, 20)
    )


def _is_g1_japanese(data: bytes) -> bool:
    """Check Gen 1 Japanese list structures."""
    return (
        _has_list_at(data, 0x2ED5, 0x302D, 30)
    )


def _detect_yellow_or_rb(data: bytes) -> str:
    """Distinguish Yellow from Red/Blue using starter byte and Pikachu friendship."""
    if _is_yellow_int(data):
        return "Yellow"
    return "Red/Blue"


def _is_yellow_int(data: bytes) -> bool:
    """Check if save is Pokemon Yellow.

    Starter byte at 0x29C3: 0x54 = Pikachu (Yellow).
    If starter is 0x00 (new game), check Pikachu friendship at 0x271C;
    non-zero indicates Yellow.
    """
    if len(data) <= 0x29C3:
        return False

    starter = data[0x29C3]
    if starter == 0x54:
        return True
    if starter == 0x00 and len(data) > 0x271C:
        return data[0x271C] != 0x00
    return False


# ---------------------------------------------------------------------------
# Gen 2 detection
# ---------------------------------------------------------------------------

def _try_g2(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 2 international save file (32 KiB)."""
    # Gold/Silver international
    if _has_list_at(data, 0x288A, 0x2D6C, 20):
        return (2, "Gold/Silver")
    # Crystal international
    if _has_list_at(data, 0x2865, 0x2D10, 20):
        return (2, "Crystal")
    # Gold/Silver Korean
    if _has_list_at(data, 0x2DAE, 0x28CC, 20):
        return (2, "Gold/Silver")
    return None


def _try_g2_japanese(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 2 Japanese save file (64 KiB)."""
    # Gold/Silver Japanese
    if _has_list_at(data, 0x2D10, 0x283E, 30):
        return (2, "Gold/Silver")
    # Crystal Japanese
    if _has_list_at(data, 0x2D10, 0x281A, 30):
        return (2, "Crystal")
    return None


# ---------------------------------------------------------------------------
# Gen 1-2 list validation helpers
# ---------------------------------------------------------------------------

def _has_list_at(data: bytes, offset1: int, offset2: int, max_count: int) -> bool:
    """Check that BOTH offsets contain valid Gen 1/2 Pokemon list structures."""
    return (
        _is_list_valid_g12(data, offset1, max_count)
        and _is_list_valid_g12(data, offset2, max_count)
    )


def _is_list_valid_g12(data: bytes, offset: int, max_count: int) -> bool:
    """Validate a Gen 1/2 Pokemon list at a given offset.

    A valid list has:
    - count byte at offset <= max_count
    - terminator byte 0xFF at offset + 1 + count
    """
    if offset >= len(data):
        return False

    count = data[offset]
    if count > max_count:
        return False

    terminator_offset = offset + 1 + count
    if terminator_offset >= len(data):
        return False

    return data[terminator_offset] == 0xFF


# ---------------------------------------------------------------------------
# Gen 3 detection
# ---------------------------------------------------------------------------

def _try_g3(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 3 save file.

    Full-size saves (128 KiB) have two slots: A at 0x0000, B at 0xE000.
    Half-size saves (64 KiB) only have slot A at 0x0000.
    """
    # Determine which slots to check based on file size
    slots = [0x0000]
    if len(data) >= SIZE_G3RAW:
        slots.append(0xE000)

    for slot_offset in slots:
        if _is_all_main_sectors_present(data, slot_offset):
            small_offset = _find_section_offset(data, slot_offset, section_id=0)
            if small_offset is not None:
                version = _get_version_g3(data, small_offset)
                return (3, version)
    return None


def _is_all_main_sectors_present(data: bytes, slot_offset: int) -> bool:
    """Verify all 14 sector IDs (0-13) are present in a Gen 3 save slot.

    Each sector is 4096 bytes. The Section ID is a uint16 at offset 0xFF4
    within each sector. All IDs 0-13 must be present (bitmask == 0x3FFF).
    """
    seen = 0
    for i in range(14):
        sector_start = slot_offset + i * _G3_SECTOR_SIZE
        id_offset = sector_start + 0xFF4

        if id_offset + 2 > len(data):
            return False

        section_id = struct.unpack_from("<H", data, id_offset)[0]
        if section_id > 13:
            return False
        seen |= 1 << section_id

    return seen == 0x3FFF


def _find_section_offset(data: bytes, slot_offset: int, section_id: int) -> int | None:
    """Find the physical offset of a given section ID within a Gen 3 save slot."""
    for i in range(14):
        sector_start = slot_offset + i * _G3_SECTOR_SIZE
        id_offset = sector_start + 0xFF4

        if id_offset + 2 > len(data):
            continue

        sid = struct.unpack_from("<H", data, id_offset)[0]
        if sid == section_id:
            return sector_start
    return None


def _get_version_g3(data: bytes, small_offset: int) -> str:
    """Determine Gen 3 game version from Section 0 data.

    Reads uint32 at offset 0xAC within Section 0:
    - 0x00000001 -> FireRed/LeafGreen
    - 0x00000000 -> Ruby/Sapphire
    - Other -> check bytes 0x890-0xF2C for non-zero data to distinguish Emerald
    """
    version_offset = small_offset + 0xAC
    if version_offset + 4 > len(data):
        return "Unknown Gen 3"

    version_val = struct.unpack_from("<I", data, version_offset)[0]

    if version_val == 1:
        return "FireRed/LeafGreen"
    if version_val == 0:
        # Could be Ruby/Sapphire or Emerald with zero at this offset.
        # Check the Emerald-specific range for non-zero data.
        if _has_nonzero_in_range(data, small_offset + 0x890, small_offset + 0xF2C):
            return "Emerald"
        return "Ruby/Sapphire"

    # Non-zero, non-one value: likely Emerald
    if _has_nonzero_in_range(data, small_offset + 0x890, small_offset + 0xF2C):
        return "Emerald"
    return "Ruby/Sapphire"


def _has_nonzero_in_range(data: bytes, start: int, end: int) -> bool:
    """Check if any byte in the given range is non-zero."""
    end = min(end, len(data))
    start = max(start, 0)
    for i in range(start, end):
        if data[i] != 0:
            return True
    return False


# ---------------------------------------------------------------------------
# Gen 4 detection
# ---------------------------------------------------------------------------

def _try_g4(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 4 save file.

    Checks Diamond/Pearl, Platinum, and HeartGold/SoulSilver in order.
    First match wins.
    """
    result = _is_g4_dp(data)
    if result is not None:
        return result

    result = _is_g4_pt(data)
    if result is not None:
        return result

    result = _is_g4_hgss(data)
    if result is not None:
        return result

    return None


def _is_g4_dp(data: bytes) -> tuple[int, str] | None:
    """Check if save matches Diamond/Pearl format."""
    if _is_valid_general_footer_4(data, _G4_DP_GENERAL_SIZE):
        return (4, "Diamond/Pearl")
    return None


def _is_g4_pt(data: bytes) -> tuple[int, str] | None:
    """Check if save matches Platinum format."""
    if _is_valid_general_footer_4(data, _G4_PT_GENERAL_SIZE):
        return (4, "Platinum")
    return None


def _is_g4_hgss(data: bytes) -> tuple[int, str] | None:
    """Check if save matches HeartGold/SoulSilver format."""
    if _is_valid_general_footer_4(data, _G4_HGSS_GENERAL_SIZE):
        return (4, "HeartGold/SoulSilver")
    return None


def _is_valid_general_footer_4(data: bytes, general_size: int) -> bool:
    """Validate Gen 4 general block footer.

    Gen 4 saves have two copies: primary (0x0) and backup (0x40000).
    Each block has a 12-byte footer at the end:
    - offset -0xC: block_size (uint32, must match general_size)
    - offset -0x8: SDK date stamp (uint32, e.g. 0x20060623)
    - offset -0x4: CRC/checksum (uint32)

    We validate by checking the block_size field matches in EITHER
    the primary or backup copy.
    """
    for block_base in (0x0, 0x40000):
        footer_offset = block_base + general_size
        size_offset = footer_offset - 0xC

        if size_offset + 4 > len(data) or size_offset < 0:
            continue

        block_size = struct.unpack_from("<I", data, size_offset)[0]
        if block_size == general_size:
            # Also verify the date stamp at -0x8 is non-zero
            # (rules out blank/zeroed regions)
            stamp_offset = footer_offset - 0x8
            if stamp_offset + 4 <= len(data):
                stamp = struct.unpack_from("<I", data, stamp_offset)[0]
                if stamp != 0:
                    return True

    return False


# ---------------------------------------------------------------------------
# Gen 5 detection
# ---------------------------------------------------------------------------

def _try_g5(data: bytes) -> tuple[int, str] | None:
    """Try to identify data as a Gen 5 save file.

    Checks Black/White first, then Black 2/White 2.
    """
    if _is_valid_footer_5(data, _G5_BW_MAIN_SIZE, _G5_BW_INFO_LENGTH):
        return (5, "Black/White")
    if _is_valid_footer_5(data, _G5_B2W2_MAIN_SIZE, _G5_B2W2_INFO_LENGTH):
        return (5, "Black 2/White 2")
    return None


def _is_valid_footer_5(data: bytes, main_size: int, info_length: int) -> bool:
    """Validate Gen 5 save footer using CRC-16-CCITT.

    The footer block is located at main_size - 0x100.
    The stored CRC-16 is at the beginning of the info block,
    and is validated against the computed CRC of the info data.
    """
    # Import CRC-16 from the crypto module
    try:
        from pokesave.crypto.gen4 import crc16_ccitt
    except ImportError:
        # If crypto module not yet implemented, we cannot validate
        return False

    footer_offset = main_size - 0x100
    if footer_offset < 0 or footer_offset + info_length > len(data):
        return False

    # The footer slice is info_length + 0x10 bytes.
    # The stored CRC-16 is the last 2 bytes of that slice (at offset info_length + 0x0E).
    # The CRC is computed over the first info_length bytes of the slice.
    crc_offset = footer_offset + info_length + 0x0E
    if crc_offset + 2 > len(data):
        return False

    stored_crc = struct.unpack_from("<H", data, crc_offset)[0]

    # Compute CRC over the first info_length bytes of the footer
    info_data = data[footer_offset : footer_offset + info_length]
    computed_crc = crc16_ccitt(info_data)

    return stored_crc == computed_crc
