"""Gen IV and Gen V character encoding.

Gen 4 (Diamond/Pearl/Platinum/HeartGold/SoulSilver) uses a proprietary 16-bit
encoding.  Each character is a little-endian u16 value.  The terminator is
0xFFFF.

The international (non-Japanese) character table maps:
  0x0121-0x012A  →  0-9
  0x012B-0x0144  →  A-Z
  0x0145-0x015E  →  a-z
  0x015F-0x019E  →  Latin Extended (À-ÿ, matching Unicode U+00C0-U+00FF)
  0x01DE         →  space
  Other values   →  punctuation and special characters

Gen 5 (Black/White/Black2/White2) uses standard UTF-16-LE with a 0xFFFF
terminator.  This is handled by ``decode_string_gen5()``.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_IV)
  - https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_V)
  - PKHeX.Core StringConverter4Util.cs
"""

from __future__ import annotations

import struct

# ---------------------------------------------------------------------------
# Gen 4 terminator
# ---------------------------------------------------------------------------
TERMINATOR: int = 0xFFFF

# ---------------------------------------------------------------------------
# Gen 4 character lookup table (international / English)
# ---------------------------------------------------------------------------
# Built from verified save data and cross-referenced with PKHeX tables.

_G4_CHAR_TABLE: dict[int, str] = {}

# Digits 0-9 at 0x0121-0x012A
for _i in range(10):
    _G4_CHAR_TABLE[0x0121 + _i] = chr(ord('0') + _i)

# Uppercase A-Z at 0x012B-0x0144
for _i in range(26):
    _G4_CHAR_TABLE[0x012B + _i] = chr(ord('A') + _i)

# Lowercase a-z at 0x0145-0x015E
for _i in range(26):
    _G4_CHAR_TABLE[0x0145 + _i] = chr(ord('a') + _i)

# Latin Extended characters À-ÿ at 0x015F-0x019E (maps to Unicode U+00C0-U+00FF)
for _i in range(64):
    _G4_CHAR_TABLE[0x015F + _i] = chr(0x00C0 + _i)

# Space
_G4_CHAR_TABLE[0x01DE] = ' '

# Common punctuation (from PKHeX character tables)
_G4_CHAR_TABLE[0x01AB] = '!'
_G4_CHAR_TABLE[0x01AC] = '?'
_G4_CHAR_TABLE[0x01AE] = '.'
_G4_CHAR_TABLE[0x01AF] = '-'
_G4_CHAR_TABLE[0x01B0] = '\u00B7'  # middle dot ·
_G4_CHAR_TABLE[0x01B1] = '\u2026'  # ellipsis …
_G4_CHAR_TABLE[0x01B4] = '\u2018'  # left single quote '
_G4_CHAR_TABLE[0x01B5] = '\u2019'  # right single quote '
_G4_CHAR_TABLE[0x01B2] = '\u00AB'  # «
_G4_CHAR_TABLE[0x01B3] = '\u00BB'  # »
_G4_CHAR_TABLE[0x01AD] = ','
_G4_CHAR_TABLE[0x01C0] = '/'
_G4_CHAR_TABLE[0x01DB] = '\u2642'  # ♂
_G4_CHAR_TABLE[0x01DC] = '\u2640'  # ♀
_G4_CHAR_TABLE[0x01D0] = '&'
_G4_CHAR_TABLE[0x01D1] = '+'

# Cleanup loop variables
del _i


def _g4_char(value: int) -> str:
    """Convert a Gen 4 character code to a Unicode character."""
    ch = _G4_CHAR_TABLE.get(value)
    if ch is not None:
        return ch
    # Fallback: return '?' for unknown codes
    if value == 0x0000:
        return ''
    return '?'


def decode_string(data: bytes) -> str:
    """Decode Gen 4 16-bit encoded bytes to a Python string.

    Reads *data* as a sequence of little-endian unsigned 16-bit integers.
    Stops at the first 0xFFFF terminator or at the end of *data*.

    Each u16 value is mapped through the Gen 4 character table to produce
    the correct Unicode character.

    Args:
        data: Raw bytes from the save file.  Length should be even (pairs
              of bytes); if the length is odd the trailing byte is ignored.

    Returns:
        The decoded string.  Returns an empty string for empty or
        insufficient input.
    """
    if not data:
        return ""

    chars: list[str] = []
    pair_count = len(data) // 2

    for i in range(pair_count):
        value = struct.unpack_from("<H", data, i * 2)[0]
        if value == TERMINATOR:
            break
        chars.append(_g4_char(value))

    return "".join(chars)


def decode_string_gen5(data: bytes) -> str:
    """Decode Gen 5 UTF-16-LE encoded bytes to a Python string.

    Gen 5 uses standard UTF-16-LE encoding.  The string is terminated by
    the u16 value 0xFFFF (which corresponds to the Unicode non-character
    U+FFFF).

    Args:
        data: Raw bytes from the save file.  Length should be even; a
              trailing odd byte is ignored.

    Returns:
        The decoded string.  Returns an empty string for empty input.
    """
    if not data:
        return ""

    # Trim to an even number of bytes.
    usable = len(data) & ~1
    if usable == 0:
        return ""

    # Decode the whole chunk as UTF-16-LE, then split at the terminator.
    # U+FFFF is the terminator character.
    try:
        decoded = data[:usable].decode("utf-16-le", errors="replace")
    except (UnicodeDecodeError, ValueError):
        # Extremely unlikely with errors="replace", but be safe.
        return ""

    # Split at the terminator character (U+FFFF).
    terminator_char = "\uFFFF"
    idx = decoded.find(terminator_char)
    if idx != -1:
        return decoded[:idx]
    return decoded
