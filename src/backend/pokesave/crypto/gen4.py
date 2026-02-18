"""Gen IV encryption, block shuffling, and CRC-16-CCITT routines.

Gen 4 Pokemon data structure (136 bytes in box, 236 in party):
  - 8 bytes header (PID + padding/checksum) -- NOT encrypted
  - 128 bytes block data (4 x 32-byte blocks A,B,C,D) -- encrypted
  - 100 bytes battle stats (party only) -- encrypted with different seed

Block data encryption: PRNG-seeded XOR, seed = stored checksum value.
Battle stats encryption: PRNG-seeded XOR, seed = personality value (PID).
Block order: determined by ((PID >> 13) & 0x1F) % 24.

PRNG is the standard GBA/NDS Linear Congruential RNG:
    seed = seed * 0x41C64E6D + 0x6073

Save-level integrity uses CRC-16-CCITT (poly 0x1021, init 0xFFFF).

References:
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_IV)
  - https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_IV)
  - PKHeX.Core PokeCrypto4.cs
"""

import struct


# The 24 permutations of blocks A, B, C, D.
# Index = ((PID >> 13) & 0x1F) % 24.
# The string tells you which block occupies each 32-byte slot in order.
BLOCK_ORDER: list[str] = [
    "ABCD",  # 0
    "ABDC",  # 1
    "ACBD",  # 2
    "ACDB",  # 3
    "ADBC",  # 4
    "ADCB",  # 5
    "BACD",  # 6
    "BADC",  # 7
    "BCAD",  # 8
    "BCDA",  # 9
    "BDAC",  # 10
    "BDCA",  # 11
    "CABD",  # 12
    "CADB",  # 13
    "CBAD",  # 14
    "CBDA",  # 15
    "CDAB",  # 16
    "CDBA",  # 17
    "DABC",  # 18
    "DACB",  # 19
    "DBAC",  # 20
    "DBCA",  # 21
    "DCAB",  # 22
    "DCBA",  # 23
]

# Map block letter to its canonical index: A=0, B=1, C=2, D=3
_LETTER_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


def lcrng_next(seed: int) -> int:
    """Advance the Linear Congruential RNG by one step.

    The GBA/NDS LCRNG formula is:
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF

    Args:
        seed: Current 32-bit PRNG state.

    Returns:
        Next 32-bit PRNG state.
    """
    return (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF


def _prng_decrypt(encrypted: bytes, seed: int) -> bytes:
    """Decrypt a byte sequence using PRNG-seeded XOR.

    For each 16-bit little-endian word in the data:
      1. Advance the PRNG
      2. XOR the word with the upper 16 bits of the new PRNG state

    If the data has an odd number of bytes, the last byte is preserved as-is
    (this matches the game's behavior of only processing complete u16 words).

    Args:
        encrypted: The encrypted byte data.
        seed: Initial PRNG seed (32-bit).

    Returns:
        Decrypted bytes of the same length as input.
    """
    num_words = len(encrypted) // 2
    words = list(struct.unpack(f"<{num_words}H", encrypted[: num_words * 2]))

    state = seed & 0xFFFFFFFF
    for i in range(num_words):
        state = lcrng_next(state)
        words[i] ^= (state >> 16) & 0xFFFF

    result = struct.pack(f"<{num_words}H", *words)

    # Preserve any trailing odd byte
    if len(encrypted) % 2 == 1:
        result += encrypted[-1:]

    return result


def decrypt_pokemon_blocks(encrypted: bytes, checksum: int) -> bytes:
    """Decrypt the 128-byte Pokemon block data.

    The block data consists of 64 u16 words (128 bytes). The PRNG is seeded
    with the Pokemon's stored checksum value, and each word is XOR'd with the
    upper 16 bits of successive PRNG outputs.

    Args:
        encrypted: 128 bytes of encrypted block data.
        checksum: The stored 16-bit checksum (used as PRNG seed).

    Returns:
        128 bytes of decrypted block data.

    Raises:
        ValueError: If encrypted data is not exactly 128 bytes.
    """
    if len(encrypted) != 128:
        raise ValueError(f"Expected 128 bytes of block data, got {len(encrypted)}")

    return _prng_decrypt(encrypted, checksum)


def decrypt_battle_stats(encrypted: bytes, pid: int) -> bytes:
    """Decrypt battle stats for a party Pokemon (Gen 4).

    Battle stats are appended to the 136-byte box data in party Pokemon.
    In Gen 4, this section is 100 bytes. The PRNG is seeded with the
    Pokemon's personality value (PID).

    Args:
        encrypted: 100 bytes of encrypted battle stat data.
        pid: The Pokemon's 32-bit personality value.

    Returns:
        100 bytes of decrypted battle stat data.

    Raises:
        ValueError: If encrypted data is not exactly 100 bytes.
    """
    if len(encrypted) != 100:
        raise ValueError(
            f"Expected 100 bytes of battle stat data, got {len(encrypted)}"
        )

    return _prng_decrypt(encrypted, pid)


def get_block_order(pid: int) -> tuple[int, int, int, int]:
    """Return byte offsets for blocks (A, B, C, D) in the decrypted data.

    The 128 bytes of decrypted Pokemon data contain four 32-byte blocks
    whose order depends on ((PID >> 13) & 0x1F) % 24. This function
    returns a 4-tuple where:
      - index 0 = byte offset of block A
      - index 1 = byte offset of block B
      - index 2 = byte offset of block C
      - index 3 = byte offset of block D

    Each offset is one of (0, 32, 64, 96).

    Args:
        pid: The Pokemon's 32-bit personality value.

    Returns:
        Tuple of (a_offset, b_offset, c_offset, d_offset).
    """
    index = ((pid >> 13) & 0x1F) % 24
    order_str = BLOCK_ORDER[index]

    offsets = [0, 0, 0, 0]
    for position, letter in enumerate(order_str):
        canonical_index = _LETTER_INDEX[letter]
        offsets[canonical_index] = position * 32

    return (offsets[0], offsets[1], offsets[2], offsets[3])


def pokemon_checksum(decrypted_data: bytes) -> int:
    """Compute the Pokemon data checksum over decrypted block data.

    Sums all 128 bytes interpreted as 16-bit little-endian words (64 words)
    and returns the lower 16 bits.

    Args:
        decrypted_data: 128 bytes of decrypted block data.

    Returns:
        16-bit checksum value.

    Raises:
        ValueError: If data is not exactly 128 bytes.
    """
    if len(decrypted_data) != 128:
        raise ValueError(
            f"Expected 128 bytes of decrypted data, got {len(decrypted_data)}"
        )

    words = struct.unpack("<64H", decrypted_data)
    return sum(words) & 0xFFFF


def crc16_ccitt(data: bytes) -> int:
    """Compute CRC-16-CCITT checksum.

    Uses polynomial 0x1021 with initial value 0xFFFF, processing each byte
    MSB first (big-endian bit order). This matches the standard CRC-16/CCITT-FALSE
    variant used by the NDS Pokemon games.

    Args:
        data: The byte sequence to checksum.

    Returns:
        16-bit CRC value.
    """
    crc = 0xFFFF

    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return crc
