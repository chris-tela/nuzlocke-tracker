"""Gen I/II character encoding.

Gen 1 and Gen 2 share the same proprietary single-byte encoding.
Gen 2 is backward compatible with Gen 1's character map.
String terminator is 0x50.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_I)
  - https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_II)
"""

# ---------------------------------------------------------------------------
# International character map
# ---------------------------------------------------------------------------
# Byte value -> character.  Built programmatically where ranges are contiguous,
# then individual special characters are inserted.

_INTL_CHARMAP: dict[int, str] = {}

# 0x7F = space
_INTL_CHARMAP[0x7F] = " "

# 0x80-0x99 = A-Z  (26 letters)
for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _INTL_CHARMAP[0x80 + i] = ch

# 0xA0-0xB9 = a-z  (26 letters)
for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _INTL_CHARMAP[0xA0 + i] = ch

# 0xF6-0xFF = 0-9  (10 digits)
for i, ch in enumerate("0123456789"):
    _INTL_CHARMAP[0xF6 + i] = ch

# Special characters
_INTL_CHARMAP[0xE0] = "'"   # apostrophe
_INTL_CHARMAP[0xE1] = "PK"  # PK ligature
_INTL_CHARMAP[0xE2] = "MN"  # MN ligature
_INTL_CHARMAP[0xE3] = "-"   # dash
_INTL_CHARMAP[0xE6] = "?"   # question mark
_INTL_CHARMAP[0xE7] = "!"   # exclamation mark
_INTL_CHARMAP[0xE8] = "."   # period
_INTL_CHARMAP[0xEF] = "\u2642"  # male sign
_INTL_CHARMAP[0xF5] = "\u2640"  # female sign
_INTL_CHARMAP[0xF4] = ","   # comma
_INTL_CHARMAP[0xF0] = "\u00A5"  # yen sign
_INTL_CHARMAP[0xF1] = "\u00D7"  # multiplication sign
_INTL_CHARMAP[0xF3] = "/"   # slash

# Additional international characters commonly encountered in Gen 1/2 ROMs.
# These fill in gaps in the table so that real-world save data decodes more
# completely.  (Values sourced from Bulbapedia's full encoding table.)
_INTL_CHARMAP[0x9A] = "("
_INTL_CHARMAP[0x9B] = ")"
_INTL_CHARMAP[0x9C] = ":"
_INTL_CHARMAP[0x9D] = ";"
_INTL_CHARMAP[0xBA] = "\u00C9"  # E-acute, used in "POKeMON"
_INTL_CHARMAP[0xE4] = "\u2019"  # right single quote (alternate apostrophe)
_INTL_CHARMAP[0xE5] = "\u2019"  # right single quote (duplicate slot in some ROMs)

# ---------------------------------------------------------------------------
# Japanese character map
# ---------------------------------------------------------------------------
# Gen 1/2 Japanese encoding maps bytes to katakana and hiragana.
# 0x80-0xC5 covers the full katakana set (including small kana variants).
# 0x60-0x79 covers a hiragana subset.

_JP_CHARMAP: dict[int, str] = {}

# 0x7F = space (same as international)
_JP_CHARMAP[0x7F] = " "

# --- Katakana: 0x80-0xC5 ---
# Standard katakana order used in the Game Boy character ROM.
_KATAKANA = (
    # 0x80-0x84: a-row
    "\u30A2",  #ア
    "\u30A4",  # イ
    "\u30A6",  # ウ
    "\u30A8",  # エ
    "\u30AA",  # オ
    # 0x85-0x89: ka-row
    "\u30AB",  # カ
    "\u30AD",  # キ
    "\u30AF",  # ク
    "\u30B1",  # ケ
    "\u30B3",  # コ
    # 0x8A-0x8E: sa-row
    "\u30B5",  # サ
    "\u30B7",  # シ
    "\u30B9",  # ス
    "\u30BB",  # セ
    "\u30BD",  # ソ
    # 0x8F-0x93: ta-row
    "\u30BF",  # タ
    "\u30C1",  # チ
    "\u30C4",  # ツ
    "\u30C6",  # テ
    "\u30C8",  # ト
    # 0x94-0x98: na-row
    "\u30CA",  # ナ
    "\u30CB",  # ニ
    "\u30CC",  # ヌ
    "\u30CD",  # ネ
    "\u30CE",  # ノ
    # 0x99-0x9D: ha-row
    "\u30CF",  # ハ
    "\u30D2",  # ヒ
    "\u30D5",  # フ
    "\u30D8",  # ヘ
    "\u30DB",  # ホ
    # 0x9E-0xA2: ma-row
    "\u30DE",  # マ
    "\u30DF",  # ミ
    "\u30E0",  # ム
    "\u30E1",  # メ
    "\u30E2",  # モ
    # 0xA3-0xA5: ya-row
    "\u30E4",  # ヤ
    "\u30E6",  # ユ
    "\u30E8",  # ヨ
    # 0xA6-0xAA: ra-row
    "\u30E9",  # ラ
    "\u30EA",  # リ
    "\u30EB",  # ル
    "\u30EC",  # レ
    "\u30ED",  # ロ
    # 0xAB-0xAC: wa-row
    "\u30EF",  # ワ
    "\u30F2",  # ヲ
    # 0xAD: n
    "\u30F3",  # ン
    # 0xAE-0xB3: voiced/semi-voiced marks and small kana
    "\u30C3",  # ッ (small tsu)
    "\u30A1",  # ァ (small a)
    "\u30A3",  # ィ (small i)
    "\u30A5",  # ゥ (small u)
    "\u30A7",  # ェ (small e)
    "\u30A9",  # ォ (small o)
    # 0xB4-0xB5: small ya/yu/yo
    "\u30E3",  # ャ (small ya)
    "\u30E5",  # ュ (small yu)
    # 0xB6
    "\u30E7",  # ョ (small yo)
    # 0xB7-0xBB: ga-row (voiced)
    "\u30AC",  # ガ
    "\u30AE",  # ギ
    "\u30B0",  # グ
    "\u30B2",  # ゲ
    "\u30B4",  # ゴ
    # 0xBC-0xC0: za-row (voiced)
    "\u30B6",  # ザ
    "\u30B8",  # ジ
    "\u30BA",  # ズ
    "\u30BC",  # ゼ
    "\u30BE",  # ゾ
    # 0xC1-0xC5: da-row (voiced)
    "\u30C0",  # ダ
    "\u30C2",  # ヂ
    "\u30C5",  # ヅ
    "\u30C7",  # デ
    "\u30C9",  # ド
)

for i, ch in enumerate(_KATAKANA):
    _JP_CHARMAP[0x80 + i] = ch

# --- Hiragana subset: 0x60-0x79 ---
_HIRAGANA = (
    # 0x60-0x64: a-row
    "\u3042",  # あ
    "\u3044",  # い
    "\u3046",  # う
    "\u3048",  # え
    "\u304A",  # お
    # 0x65-0x69: ka-row
    "\u304B",  # か
    "\u304D",  # き
    "\u304F",  # く
    "\u3051",  # け
    "\u3053",  # こ
    # 0x6A-0x6E: sa-row
    "\u3055",  # さ
    "\u3057",  # し
    "\u3059",  # す
    "\u305B",  # せ
    "\u305D",  # そ
    # 0x6F-0x73: ta-row
    "\u305F",  # た
    "\u3061",  # ち
    "\u3064",  # つ
    "\u3066",  # て
    "\u3068",  # と
    # 0x74-0x78: na-row
    "\u306A",  # な
    "\u306B",  # に
    "\u306C",  # ぬ
    "\u306D",  # ね
    "\u306E",  # の
    # 0x79: ha (just the first of the ha-row in this range)
    "\u306F",  # は
)

for i, ch in enumerate(_HIRAGANA):
    _JP_CHARMAP[0x60 + i] = ch

# Japanese digits (same byte positions as international)
for i, ch in enumerate("0123456789"):
    _JP_CHARMAP[0xF6 + i] = ch

# Japanese special characters that mirror international positions
_JP_CHARMAP[0xE0] = "'"
_JP_CHARMAP[0xE1] = "PK"
_JP_CHARMAP[0xE2] = "MN"
_JP_CHARMAP[0xE3] = "-"
_JP_CHARMAP[0xE6] = "?"
_JP_CHARMAP[0xE7] = "!"
_JP_CHARMAP[0xE8] = "."
_JP_CHARMAP[0xEF] = "\u2642"  # male
_JP_CHARMAP[0xF5] = "\u2640"  # female
_JP_CHARMAP[0xF4] = ","
_JP_CHARMAP[0xF0] = "\u00A5"  # yen
_JP_CHARMAP[0xF1] = "\u00D7"  # multiplication
_JP_CHARMAP[0xF3] = "/"

# Dakuten / handakuten marks (useful for Japanese text)
_JP_CHARMAP[0x05] = "\u309B"  # dakuten
_JP_CHARMAP[0x06] = "\u309C"  # handakuten

# ---------------------------------------------------------------------------
# Terminator byte
# ---------------------------------------------------------------------------
TERMINATOR = 0x50


def decode_string(data: bytes, japanese: bool = False) -> str:
    """Decode Gen 1/2 encoded bytes to a Python string.

    The proprietary encoding uses 0x50 as the string terminator.
    Decoding stops at the first terminator byte or at the end of *data*,
    whichever comes first.

    Args:
        data: Raw bytes from the save file.
        japanese: If True, use the Japanese (kana) character map instead of
                  the international (Latin) character map.

    Returns:
        The decoded string.  Unknown bytes are replaced with '?'.
    """
    if not data:
        return ""

    charmap = _JP_CHARMAP if japanese else _INTL_CHARMAP
    chars: list[str] = []

    for byte in data:
        if byte == TERMINATOR:
            break
        ch = charmap.get(byte)
        if ch is not None:
            chars.append(ch)
        else:
            chars.append("?")

    return "".join(chars)
