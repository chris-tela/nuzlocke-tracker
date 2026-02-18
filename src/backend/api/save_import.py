"""Save file parsing and data cleansing for import into nuzlocke-tracker."""

import logging
import sys
from pathlib import Path

# Ensure local backend packages (including `pokesave`) are importable
# regardless of whether API is launched as `api.main` or `src.backend.api.main`.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pokesave.detect import detect
from pokesave.models import SaveFile, Pokemon as PokesavePokemon

logger = logging.getLogger(__name__)

# Mapping from pokesave's combined game names to nuzlocke-tracker DB version names
SAVE_GAME_TO_VERSIONS: dict[str, list[str]] = {
    "Red/Blue": ["red", "blue"],
    "Yellow": ["yellow"],
    "Gold/Silver": ["gold", "silver"],
    "Crystal": ["crystal"],
    "Ruby/Sapphire": ["ruby", "sapphire"],
    "Emerald": ["emerald"],
    "FireRed/LeafGreen": ["firered", "leafgreen"],
    "Diamond/Pearl": ["diamond", "pearl"],
    "Platinum": ["platinum"],
    "HeartGold/SoulSilver": ["heartgold", "soulsilver"],
    "Black/White": ["black", "white"],
    "Black 2/White 2": ["black-2", "white-2"],
}

VALID_NATURES = {
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold", "Docile", "Relaxed", "Impish", "Lax",
    "Timid", "Hasty", "Serious", "Jolly", "Naive",
    "Modest", "Mild", "Quiet", "Bashful", "Rash",
    "Calm", "Gentle", "Sassy", "Careful", "Quirky",
}


def parse_save_file(data: bytes) -> dict:
    """Parse raw .sav bytes and return a cleansed preview dict.

    Returns dict with keys: generation, game, compatible_versions, trainer_name, pokemon

    Raises:
        ValueError: If the file cannot be parsed.
    """
    generation, game = detect(data)
    parser = _get_parser(generation)
    save: SaveFile = parser.parse(data)

    compatible_versions = SAVE_GAME_TO_VERSIONS.get(game, [])
    if not compatible_versions:
        logger.warning(f"No version mapping for game '{game}', using lowercase")
        compatible_versions = [game.lower().replace(" ", "-")]

    all_pokemon = []
    for pkmn in save.party:
        all_pokemon.append(_cleanse_pokemon(pkmn))
    for box_name, box_pokemon in save.boxes.items():
        for pkmn in box_pokemon:
            all_pokemon.append(_cleanse_pokemon(pkmn))

    return {
        "generation": generation,
        "game": game,
        "compatible_versions": compatible_versions,
        "trainer_name": save.trainer.name,
        "badges": save.trainer.badges,
        "pokemon": all_pokemon,
    }


def _cleanse_pokemon(pkmn: PokesavePokemon) -> dict:
    """Convert a pokesave Pokemon model to a cleansed dict for DB import."""
    nature = None
    if pkmn.nature and pkmn.nature in VALID_NATURES:
        nature = pkmn.nature

    ability = pkmn.ability.lower() if pkmn.ability else None
    status = "Party" if pkmn.location == "party" else "Stored"
    level = max(1, min(100, pkmn.level))

    # If nickname is just the species name in ALL CAPS, it's the default — not a real nickname
    nickname = pkmn.nickname
    if nickname and nickname.upper() == nickname and nickname.upper() == pkmn.species.upper():
        nickname = None

    return {
        "poke_id": pkmn.species_id,
        "name": pkmn.species.lower(),
        "nickname": nickname,
        "nature": nature,
        "ability": ability,
        "level": level,
        "status": status,
        "caught_on": pkmn.met_location,
    }


def _get_parser(generation: int):
    """Return the parser instance for a given generation (lazy imports)."""
    parsers = {}
    try:
        from pokesave.parsers.gen1 import Gen1Parser
        parsers[1] = Gen1Parser
    except ImportError:
        pass
    try:
        from pokesave.parsers.gen2 import Gen2Parser
        parsers[2] = Gen2Parser
    except ImportError:
        pass
    try:
        from pokesave.parsers.gen3 import Gen3Parser
        parsers[3] = Gen3Parser
    except ImportError:
        pass
    try:
        from pokesave.parsers.gen4 import Gen4Parser
        parsers[4] = Gen4Parser
    except ImportError:
        pass
    try:
        from pokesave.parsers.gen5 import Gen5Parser
        parsers[5] = Gen5Parser
    except ImportError:
        pass

    parser_cls = parsers.get(generation)
    if parser_cls is None:
        raise ValueError(f"No parser available for Generation {generation}")
    return parser_cls()
