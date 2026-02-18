"""Character encoding modules for Pokemon Generations 1-5."""

from pokesave.encoding.gen1 import decode_string as decode_gen1
from pokesave.encoding.gen3 import decode_string as decode_gen3
from pokesave.encoding.gen4 import decode_string as decode_gen4
from pokesave.encoding.gen4 import decode_string_gen5 as decode_gen5

__all__ = [
    "decode_gen1",
    "decode_gen3",
    "decode_gen4",
    "decode_gen5",
]
