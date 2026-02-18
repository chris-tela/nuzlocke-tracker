"""Gen III character encoding.

Gen 3 uses a completely different proprietary single-byte encoding from
Gen 1/2.  The string terminator is 0xFF.  Space is 0x00.

Special escape byte 0xFC introduces multi-byte control sequences (text
color, player name substitution, etc.).  For our read-only parser we skip
the escape byte and its control byte, emitting '?' as a placeholder.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_III)
"""

# ---------------------------------------------------------------------------
# International character map
# ---------------------------------------------------------------------------

_INTL_CHARMAP: dict[int, str] = {}

# 0x00 = space
_INTL_CHARMAP[0x00] = " "

# 0x01-0x09: accented characters
_ACCENTED_01_09 = "ÀÁÂÇÈÉÊËÌ"
for i, ch in enumerate(_ACCENTED_01_09):
    _INTL_CHARMAP[0x01 + i] = ch

# 0x0A-0x14: more accented characters (continuing the Western European set)
_ACCENTED_0A_14 = "ÍÎÏÒÓÔŒÙÚÛÑ"
for i, ch in enumerate(_ACCENTED_0A_14):
    _INTL_CHARMAP[0x0A + i] = ch

# 0x15-0x19: lowercase accented
_ACCENTED_15_19 = "ßàáâ"
for i, ch in enumerate(_ACCENTED_15_19):
    _INTL_CHARMAP[0x15 + i] = ch

# 0x19 onward: remaining lowercase accented characters
_ACCENTED_19_ETC = {
    0x19: "ç",
    0x1A: "è",
    0x1B: "é",
    0x1C: "ê",
    0x1D: "ë",
    0x1E: "ì",
    0x1F: "í",
    0x20: "î",
    0x21: "ï",
    0x22: "ò",
    0x23: "ó",
    0x24: "ô",
    0x25: "œ",
    0x26: "ù",
    0x27: "ú",
    0x28: "û",
    0x29: "ñ",
    0x2A: "º",
    0x2B: "ª",
    0x2C: "\u00AA",  # feminine ordinal (dup -- some tables use this)
    0x2D: "&",
    0x2E: "+",
    0x34: "Lv",  # level indicator
    0x35: "=",
    0x36: ";",
    0x51: "\u00BF",  # inverted question mark
    0x52: "\u00A1",  # inverted exclamation mark
    0x53: "PK",      # PK ligature
    0x54: "MN",      # MN ligature
    0x55: "PO",      # PO ligature
    0x56: "Ke",      # Ke ligature (for "Pokemon" in some contexts)
    0x57: "\u2026",  # horizontal ellipsis (some tables)
    0x5A: "\u00C8",  # E-grave (duplicate entry)
    0x68: "\u00C0",  # A-grave
    0x79: "\u2191",  # up arrow
    0x7A: "\u2193",  # down arrow
    0x7B: "\u2190",  # left arrow
    0x7C: "\u2192",  # right arrow
}
_INTL_CHARMAP.update(_ACCENTED_19_ETC)

# 0xA1-0xAA = 0-9
for i, ch in enumerate("0123456789"):
    _INTL_CHARMAP[0xA1 + i] = ch

# 0xAB = !  0xAC = ?  0xAD = .  0xAE = -
_INTL_CHARMAP[0xAB] = "!"
_INTL_CHARMAP[0xAC] = "?"
_INTL_CHARMAP[0xAD] = "."
_INTL_CHARMAP[0xAE] = "-"
_INTL_CHARMAP[0xAF] = "\u30FB"  # middle dot (used as separator)

# 0xB0 = ellipsis  (Unicode U+2026)
_INTL_CHARMAP[0xB0] = "\u2026"

# 0xB1-0xB3: quote characters
_INTL_CHARMAP[0xB1] = "\u201C"  # left double quotation mark
_INTL_CHARMAP[0xB2] = "\u201D"  # right double quotation mark
_INTL_CHARMAP[0xB3] = "\u201C"  # left double quotation (alternate)

# 0xB4-0xB5: single quotes
_INTL_CHARMAP[0xB4] = "\u2018"  # left single quotation mark
_INTL_CHARMAP[0xB5] = "\u2019"  # right single quotation mark / apostrophe

# 0xB6-0xB9
_INTL_CHARMAP[0xB6] = "\u2642"  # male sign
_INTL_CHARMAP[0xB7] = "\u2640"  # female sign
_INTL_CHARMAP[0xB8] = ","
_INTL_CHARMAP[0xB9] = "/"

# 0xBA = colon
_INTL_CHARMAP[0xBA] = ":"

# 0xBB-0xD4 = A-Z  (26 letters)
for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _INTL_CHARMAP[0xBB + i] = ch

# 0xD5-0xEE = a-z  (26 letters)
for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _INTL_CHARMAP[0xD5 + i] = ch

# ---------------------------------------------------------------------------
# Japanese character map
# ---------------------------------------------------------------------------
# Gen 3 Japanese encoding maps bytes to half-width katakana, hiragana, and
# a subset of kanji / special characters.

_JP_CHARMAP: dict[int, str] = {}

# 0x00 = space
_JP_CHARMAP[0x00] = " "

# 0x01-0x50: katakana (ア through ン plus small kana and voiced)
_JP_KATAKANA = (
    "\u3042",  # 0x01 あ
    "\u3044",  # 0x02 い
    "\u3046",  # 0x03 う
    "\u3048",  # 0x04 え
    "\u304A",  # 0x05 お
    "\u304B",  # 0x06 か
    "\u304D",  # 0x07 き
    "\u304F",  # 0x08 く
    "\u3051",  # 0x09 け
    "\u3053",  # 0x0A こ
    "\u3055",  # 0x0B さ
    "\u3057",  # 0x0C し
    "\u3059",  # 0x0D す
    "\u305B",  # 0x0E せ
    "\u305D",  # 0x0F そ
    "\u305F",  # 0x10 た
    "\u3061",  # 0x11 ち
    "\u3064",  # 0x12 つ
    "\u3066",  # 0x13 て
    "\u3068",  # 0x14 と
    "\u306A",  # 0x15 な
    "\u306B",  # 0x16 に
    "\u306C",  # 0x17 ぬ
    "\u306D",  # 0x18 ね
    "\u306E",  # 0x19 の
    "\u306F",  # 0x1A は
    "\u3072",  # 0x1B ひ
    "\u3075",  # 0x1C ふ
    "\u3078",  # 0x1D へ
    "\u307B",  # 0x1E ほ
    "\u307E",  # 0x1F ま
    "\u307F",  # 0x20 み
    "\u3080",  # 0x21 む
    "\u3081",  # 0x22 め
    "\u3082",  # 0x23 も
    "\u3084",  # 0x24 や
    "\u3086",  # 0x25 ゆ
    "\u3088",  # 0x26 よ
    "\u3089",  # 0x27 ら
    "\u308A",  # 0x28 り
    "\u308B",  # 0x29 る
    "\u308C",  # 0x2A れ
    "\u308D",  # 0x2B ろ
    "\u308F",  # 0x2C わ
    "\u3092",  # 0x2D を
    "\u3093",  # 0x2E ん
    "\u3041",  # 0x2F ぁ
    "\u3043",  # 0x30 ぃ
    "\u3045",  # 0x31 ぅ
    "\u3047",  # 0x32 ぇ
    "\u3049",  # 0x33 ぉ
    "\u3083",  # 0x34 ゃ
    "\u3085",  # 0x35 ゅ
    "\u3087",  # 0x36 ょ
    "\u304C",  # 0x37 が
    "\u304E",  # 0x38 ぎ
    "\u3050",  # 0x39 ぐ
    "\u3052",  # 0x3A げ
    "\u3054",  # 0x3B ご
    "\u3056",  # 0x3C ざ
    "\u3058",  # 0x3D じ
    "\u305A",  # 0x3E ず
    "\u305C",  # 0x3F ぜ
    "\u305E",  # 0x40 ぞ
    "\u3060",  # 0x41 だ
    "\u3062",  # 0x42 ぢ
    "\u3065",  # 0x43 づ
    "\u3067",  # 0x44 で
    "\u3069",  # 0x45 ど
    "\u3070",  # 0x46 ば
    "\u3073",  # 0x47 び
    "\u3076",  # 0x48 ぶ
    "\u3079",  # 0x49 べ
    "\u307C",  # 0x4A ぼ
    "\u3071",  # 0x4B ぱ
    "\u3074",  # 0x4C ぴ
    "\u3077",  # 0x4D ぷ
    "\u307A",  # 0x4E ぺ
    "\u307D",  # 0x4F ぽ
    "\u3063",  # 0x50 っ
)

for i, ch in enumerate(_JP_KATAKANA):
    _JP_CHARMAP[0x01 + i] = ch

# 0x51-0xA0: katakana block
_JP_KATAKANA_BLOCK = (
    "\u30A2",  # 0x51 ア
    "\u30A4",  # 0x52 イ
    "\u30A6",  # 0x53 ウ
    "\u30A8",  # 0x54 エ
    "\u30AA",  # 0x55 オ
    "\u30AB",  # 0x56 カ
    "\u30AD",  # 0x57 キ
    "\u30AF",  # 0x58 ク
    "\u30B1",  # 0x59 ケ
    "\u30B3",  # 0x5A コ
    "\u30B5",  # 0x5B サ
    "\u30B7",  # 0x5C シ
    "\u30B9",  # 0x5D ス
    "\u30BB",  # 0x5E セ
    "\u30BD",  # 0x5F ソ
    "\u30BF",  # 0x60 タ
    "\u30C1",  # 0x61 チ
    "\u30C4",  # 0x62 ツ
    "\u30C6",  # 0x63 テ
    "\u30C8",  # 0x64 ト
    "\u30CA",  # 0x65 ナ
    "\u30CB",  # 0x66 ニ
    "\u30CC",  # 0x67 ヌ
    "\u30CD",  # 0x68 ネ
    "\u30CE",  # 0x69 ノ
    "\u30CF",  # 0x6A ハ
    "\u30D2",  # 0x6B ヒ
    "\u30D5",  # 0x6C フ
    "\u30D8",  # 0x6D ヘ
    "\u30DB",  # 0x6E ホ
    "\u30DE",  # 0x6F マ
    "\u30DF",  # 0x70 ミ
    "\u30E0",  # 0x71 ム
    "\u30E1",  # 0x72 メ
    "\u30E2",  # 0x73 モ
    "\u30E4",  # 0x74 ヤ
    "\u30E6",  # 0x75 ユ
    "\u30E8",  # 0x76 ヨ
    "\u30E9",  # 0x77 ラ
    "\u30EA",  # 0x78 リ
    "\u30EB",  # 0x79 ル
    "\u30EC",  # 0x7A レ
    "\u30ED",  # 0x7B ロ
    "\u30EF",  # 0x7C ワ
    "\u30F2",  # 0x7D ヲ
    "\u30F3",  # 0x7E ン
    "\u30C3",  # 0x7F ッ
    "\u30A1",  # 0x80 ァ
    "\u30A3",  # 0x81 ィ
    "\u30A5",  # 0x82 ゥ
    "\u30A7",  # 0x83 ェ
    "\u30A9",  # 0x84 ォ
    "\u30E3",  # 0x85 ャ
    "\u30E5",  # 0x86 ュ
    "\u30E7",  # 0x87 ョ
    "\u30AC",  # 0x88 ガ
    "\u30AE",  # 0x89 ギ
    "\u30B0",  # 0x8A グ
    "\u30B2",  # 0x8B ゲ
    "\u30B4",  # 0x8C ゴ
    "\u30B6",  # 0x8D ザ
    "\u30B8",  # 0x8E ジ
    "\u30BA",  # 0x8F ズ
    "\u30BC",  # 0x90 ゼ
    "\u30BE",  # 0x91 ゾ
    "\u30C0",  # 0x92 ダ
    "\u30C2",  # 0x93 ヂ
    "\u30C5",  # 0x94 ヅ
    "\u30C7",  # 0x95 デ
    "\u30C9",  # 0x96 ド
    "\u30D0",  # 0x97 バ
    "\u30D3",  # 0x98 ビ
    "\u30D6",  # 0x99 ブ
    "\u30D9",  # 0x9A ベ
    "\u30DC",  # 0x9B ボ
    "\u30D1",  # 0x9C パ
    "\u30D4",  # 0x9D ピ
    "\u30D7",  # 0x9E プ
    "\u30DA",  # 0x9F ペ
    "\u30DD",  # 0xA0 ポ
)

for i, ch in enumerate(_JP_KATAKANA_BLOCK):
    _JP_CHARMAP[0x51 + i] = ch

# Japanese digits and punctuation share positions with international
for i, ch in enumerate("0123456789"):
    _JP_CHARMAP[0xA1 + i] = ch

_JP_CHARMAP[0xAB] = "!"
_JP_CHARMAP[0xAC] = "?"
_JP_CHARMAP[0xAD] = "."
_JP_CHARMAP[0xAE] = "-"
_JP_CHARMAP[0xB0] = "\u2026"
_JP_CHARMAP[0xB1] = "\u300C"  # Japanese left corner bracket
_JP_CHARMAP[0xB2] = "\u300D"  # Japanese right corner bracket
_JP_CHARMAP[0xB4] = "\u2018"
_JP_CHARMAP[0xB5] = "\u2019"
_JP_CHARMAP[0xB8] = ","
_JP_CHARMAP[0xB9] = "/"
_JP_CHARMAP[0xBA] = ":"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TERMINATOR = 0xFF
ESCAPE_BYTE = 0xFC


def decode_string(data: bytes, japanese: bool = False) -> str:
    """Decode Gen 3 encoded bytes to a Python string.

    The proprietary encoding uses 0xFF as the string terminator.
    Decoding stops at the first terminator or at the end of *data*.

    Escape sequences (0xFC + control byte) are replaced with '?' for now;
    a future revision can expand them into player-name placeholders, color
    codes, etc.

    Args:
        data: Raw bytes from the save file.
        japanese: If True, use the Japanese character map.

    Returns:
        The decoded string.  Unknown bytes are replaced with '?'.
    """
    if not data:
        return ""

    charmap = _JP_CHARMAP if japanese else _INTL_CHARMAP
    chars: list[str] = []
    i = 0
    length = len(data)

    while i < length:
        byte = data[i]

        # Terminator -- stop decoding.
        if byte == TERMINATOR:
            break

        # Escape sequence -- skip escape byte + 1 control byte.
        if byte == ESCAPE_BYTE:
            chars.append("?")
            # Skip the control byte that follows, if present.
            i += 2
            continue

        ch = charmap.get(byte)
        if ch is not None:
            chars.append(ch)
        else:
            chars.append("?")

        i += 1

    return "".join(chars)
