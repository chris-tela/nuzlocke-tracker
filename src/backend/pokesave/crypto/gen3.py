"""Gen III encryption and checksum routines.

Gen 3 Pokemon data is 80 bytes total:
  - 32 bytes header (PID, OTID, nickname, etc.) -- NOT encrypted
  - 48 bytes substructure data -- encrypted with XOR(PID ^ OTID)
  - The 48 bytes contain 4 x 12-byte substructures (G, A, E, M)
    shuffled according to PID % 24

Section-level checksum uses a folded 32-bit sum.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_substructures_(Generation_III)
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_III)
"""

import struct


# The 24 permutations of the four substructures G(rowth), A(ttacks), E(Vs), M(isc).
# Index = PID % 24. The string tells you which substructure occupies each
# 12-byte slot in order: first 12 bytes, second 12 bytes, third, fourth.
SUBSTRUCTURE_ORDER: list[str] = [
    "GAEM",  # 0
    "GAME",  # 1
    "GEAM",  # 2
    "GEMA",  # 3
    "GMAE",  # 4
    "GMEA",  # 5
    "AGEM",  # 6
    "AGME",  # 7
    "AEGM",  # 8
    "AEMG",  # 9
    "AMGE",  # 10
    "AMEG",  # 11
    "EGAM",  # 12
    "EGMA",  # 13
    "EAGM",  # 14
    "EAMG",  # 15
    "EMGA",  # 16
    "EMAG",  # 17
    "MGAE",  # 18
    "MGEA",  # 19
    "MAGE",  # 20
    "MAEG",  # 21
    "MEGA",  # 22
    "MEAG",  # 23
]

# Map substructure letter to its canonical index in the output tuple:
# G=0 (Growth), A=1 (Attacks), E=2 (EVs/Condition), M=3 (Misc)
_LETTER_INDEX = {"G": 0, "A": 1, "E": 2, "M": 3}


def decrypt_pokemon_data(encrypted: bytes, personality_value: int, ot_id: int) -> bytes:
    """Decrypt 48-byte Pokemon data block using XOR with (PID ^ OTID).

    The encryption key is a 32-bit value formed by XOR-ing the personality
    value (PID) with the original trainer ID (full 32-bit OTID which packs
    both the visible TID and secret SID).

    Each 32-bit little-endian word in the 48-byte block is XOR'd with this key.

    Args:
        encrypted: 48 bytes of encrypted substructure data.
        personality_value: The Pokemon's 32-bit personality value (PID).
        ot_id: The full 32-bit OT ID (TID in lower 16, SID in upper 16).

    Returns:
        48 bytes of decrypted substructure data.

    Raises:
        ValueError: If encrypted data is not exactly 48 bytes.
    """
    if len(encrypted) != 48:
        raise ValueError(f"Expected 48 bytes of encrypted data, got {len(encrypted)}")

    key = (personality_value ^ ot_id) & 0xFFFFFFFF
    words = struct.unpack("<12I", encrypted)
    decrypted_words = [w ^ key for w in words]
    return struct.pack("<12I", *decrypted_words)


def get_substructure_order(pid: int) -> tuple[int, int, int, int]:
    """Return byte offsets for (Growth, Attacks, EVs, Misc) substructures.

    The 48 bytes of decrypted Pokemon data contain four 12-byte substructures
    whose order depends on PID % 24. This function returns a 4-tuple where:
      - index 0 = byte offset of the Growth substructure
      - index 1 = byte offset of the Attacks substructure
      - index 2 = byte offset of the EVs/Condition substructure
      - index 3 = byte offset of the Misc substructure

    Each offset is one of (0, 12, 24, 36).

    Args:
        pid: The Pokemon's 32-bit personality value.

    Returns:
        Tuple of (growth_offset, attacks_offset, evs_offset, misc_offset).
    """
    order_str = SUBSTRUCTURE_ORDER[pid % 24]

    # Build a mapping: for each canonical substructure, find its position
    # in the shuffled layout. Position * 12 = byte offset.
    offsets = [0, 0, 0, 0]
    for position, letter in enumerate(order_str):
        canonical_index = _LETTER_INDEX[letter]
        offsets[canonical_index] = position * 12

    return (offsets[0], offsets[1], offsets[2], offsets[3])


def pokemon_checksum(decrypted_data: bytes) -> int:
    """Compute the Pokemon data checksum over decrypted substructure data.

    Sums all 48 bytes interpreted as 16-bit little-endian words (24 words)
    and returns the lower 16 bits.

    Args:
        decrypted_data: 48 bytes of decrypted substructure data.

    Returns:
        16-bit checksum value.

    Raises:
        ValueError: If data is not exactly 48 bytes.
    """
    if len(decrypted_data) != 48:
        raise ValueError(
            f"Expected 48 bytes of decrypted data, got {len(decrypted_data)}"
        )

    words = struct.unpack("<24H", decrypted_data)
    return sum(words) & 0xFFFF


def section_checksum(data: bytes) -> int:
    """Compute a Gen 3 save section checksum.

    The checksum is calculated by summing the data as 32-bit little-endian
    words, then folding the 32-bit sum into 16 bits:
        result = (sum & 0xFFFF) + ((sum >> 16) & 0xFFFF)
    The final value is the lower 16 bits of that result.

    If the data length is not a multiple of 4, the trailing bytes are ignored
    (consistent with how the game processes fixed-size sections).

    Args:
        data: The section data bytes to checksum. Typically the first
              3968 bytes of each 4096-byte section (excluding the 128-byte
              footer).

    Returns:
        16-bit checksum value.
    """
    # Only process complete 32-bit words
    num_words = len(data) // 4
    words = struct.unpack(f"<{num_words}I", data[: num_words * 4])
    total = sum(words) & 0xFFFFFFFF

    # Fold upper 16 bits into lower 16 bits
    folded = (total & 0xFFFF) + ((total >> 16) & 0xFFFF)
    return folded & 0xFFFF
