"""Gen V encryption routines.

Gen 5 reuses Gen 4's PRNG-based encryption and block shuffling with
two differences:
  - Battle stats are 84 bytes (vs 100 in Gen 4)
  - Box Pokemon are 136 bytes, party Pokemon are 220 bytes (vs 236)

Block data decryption (128 bytes, seed=checksum) is identical to Gen 4.
Block ordering (((PID >> 13) & 0x1F) % 24) is identical to Gen 4.
CRC-16-CCITT is identical to Gen 4.

References:
  - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_V)
  - PKHeX.Core PokeCrypto5.cs
"""

from pokesave.crypto.gen4 import (
    BLOCK_ORDER,
    _prng_decrypt,
    crc16_ccitt,
    decrypt_pokemon_blocks,
    get_block_order,
    lcrng_next,
    pokemon_checksum,
)

# Re-export everything from gen4 that is identical in gen5
__all__ = [
    "BLOCK_ORDER",
    "lcrng_next",
    "decrypt_pokemon_blocks",
    "decrypt_battle_stats",
    "get_block_order",
    "pokemon_checksum",
    "crc16_ccitt",
]


def decrypt_battle_stats(encrypted: bytes, pid: int) -> bytes:
    """Decrypt battle stats for a party Pokemon (Gen 5).

    Same PRNG-based XOR decryption as Gen 4, but Gen 5 battle stats are
    84 bytes instead of 100.

    Args:
        encrypted: 84 bytes of encrypted battle stat data.
        pid: The Pokemon's 32-bit personality value.

    Returns:
        84 bytes of decrypted battle stat data.

    Raises:
        ValueError: If encrypted data is not exactly 84 bytes.
    """
    if len(encrypted) != 84:
        raise ValueError(
            f"Expected 84 bytes of battle stat data, got {len(encrypted)}"
        )

    return _prng_decrypt(encrypted, pid)
