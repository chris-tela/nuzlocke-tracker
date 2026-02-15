"""
Populate the Trainer table from Gen JSON data files.

Reads each JSON file, computes true stats for every trainer pokemon,
fuzzy-matches locations to routes, classifies importance, detects
level outliers, and inserts Trainer rows.

Usage:
    python populate_trainers.py
"""

import json
import os
import re
import sys
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from calc import _normalize_ivs, _calculate_stat, STAT_KEYS
from route_matching import fuzzy_match_route
from trainer_importance import classify_importance, detect_level_outliers
from db.models import Trainer, AllPokemon, Route, Gym, Version
from db.database import SessionLocal

# ---------------------------------------------------------------------------
# FILE_MAP: JSON path (relative to src/data/) -> (game_names, generation)
# ---------------------------------------------------------------------------
FILE_MAP = {
    "Gen1/RedBlue.json": (["red", "blue"], 1),
    "Gen1/Yellow.json": (["yellow"], 1),
    "Gen2/GS.json": (["gold", "silver"], 2),
    "Gen2/Crystal.json": (["crystal"], 2),
    "Gen3/RS.json": (["ruby", "sapphire"], 3),
    "Gen3/FRLG.json": (["firered", "leafgreen"], 3),
    "Gen3/Emerald.json": (["emerald"], 3),
    "Gen4/DP.json": (["diamond", "pearl"], 4),
    "Gen4/Plat.json": (["platinum"], 4),
    "Gen4/HGSS.json": (["heartgold", "soulsilver"], 4),
    "Gen5/BW.json": (["black", "white"], 5),
    "Gen5/B2W2.json": (["black 2", "white 2"], 5),
    "Gen6/XY.json": (["x", "y"], 6),
    "Gen6/ORAS.json": (["omega ruby", "alpha sapphire"], 6),
    "Gen7/SM.json": (["sun", "moon"], 7),
    "Gen7/USUM.json": (["ultra sun", "ultra moon"], 7),
    "Gen8/SS.json": (["sword", "shield"], 8),
    "Gen8/BDSP.json": (["brilliant diamond", "shining pearl"], 8),
    "Gen9/SV.json": (["scarlet", "violet"], 9),
}

# Resolve project paths relative to this script's location.
BACKEND_DIR = Path(__file__).resolve().parent          # src/backend
DATA_DIR = BACKEND_DIR.parent / "data"                 # src/data
SPRITES_DIR = DATA_DIR / "sprites"                     # src/data/sprites

# ---------------------------------------------------------------------------
# Sprite resolution: map trainer names to sprite image paths
# ---------------------------------------------------------------------------

# Map FILE_MAP keys to the sprite filename prefix used in src/data/sprites/.
SPRITE_PREFIX_MAP = {
    "Gen1/RedBlue.json": "rg",
    "Gen1/Yellow.json": "y",
    "Gen2/GS.json": "gs",
    "Gen2/Crystal.json": "gs",
    "Gen3/RS.json": "rs",
    "Gen3/FRLG.json": "frlg",
    "Gen3/Emerald.json": "rs",
    "Gen4/DP.json": "dp",
    "Gen4/Plat.json": "dp",
    "Gen4/HGSS.json": "hgss",
    "Gen5/BW.json": "bw",
    "Gen5/B2W2.json": "b2w2",
    # Gen 6+ have no sprites yet.
}

# Per-game aliases for trainer names that don't follow the standard
# normalisation rules.  Keys are (sprite_prefix, normalised_name).
_SPRITE_ALIASES: dict[tuple[str, str], str] = {
    # Gen 1 Red/Blue
    ("rg", "rival"):        "blue_1",
    ("rg", "rival_champ"):  "blue_1",
    ("rg", "surge"):        "lt_surge",
    ("rg", "pokemaniac"):   "pok_maniac",
    ("rg", "cooltrainer"):  "cooltrainer_m",
    ("rg", "jr_trainer"):   "jr_trainer_m",
    ("rg", "jr_traimer"):   "jr_trainer_m",
    ("rg", "swimmer"):      "swimmer_m",
    ("rg", "black_belt"):   "blackbelt",
    # Gen 1 Yellow
    ("y", "rival"):         "blue_1",
    ("y", "rival_champ"):   "blue_1",
    ("y", "surge"):         "lt_surge",
    ("y", "pokemaniac"):    "pok_maniac",
    ("y", "cooltrainer"):   "cooltrainer_m",
    ("y", "jr_trainer"):    "jr_trainer_m",
    ("y", "jr_traimer"):    "jr_trainer_m",
    ("y", "swimmer"):       "swimmer_m",
    ("y", "black_belt"):    "blackbelt",
    # Gen 2 GS / Crystal
    ("gs", "rival"):        "silver_1",
    ("gs", "pkmn_trainer_red"): "red",
    ("gs", "pokefan"):      "pok_fan_m",
    ("gs", "pokéfan"):      "pok_fan_m",
    ("gs", "pokemaniac"):   "pok_maniac",
    ("gs", "cooltrainer"):  "cooltrainer_m",
    ("gs", "cool_trainer"):  "cooltrainer_m",
    ("gs", "swimmer"):      "swimmer_m",
    ("gs", "swimmer_f"):    "swimmer_m",
    ("gs", "schoolboy"):    "school_kid_m",
    ("gs", "school_kid"):   "school_kid_m",
    ("gs", "rocket_grunt"): "rocket_grunt_m",
    ("gs", "grunt"):        "rocket_grunt_m",
    ("gs", "blackbelt"):    "black_belt",
    ("gs", "fire_breather"): "firebreather",
    ("gs", "firebreather"): "firebreather",
    ("gs", "burgular"):     "burglar",
    ("gs", "border"):       "boarder",
    ("gs", "birdkeeper"):   "bird_keeper",
    ("gs", "picknicker"):   "picnicker",
    ("gs", "surge"):        "lt_surge",
    ("gs", "poke_maniac"):  "pok_maniac",
    ("gs", "pshycic"):      "psychic",
    ("gs", "rocket_exec"):  "rocket_grunt_m",
    ("gs", "twins"):        "twins",
    ("gs", "fisher"):       "fisherman",
    ("gs", "amy"):          "twins",
    ("gs", "jo"):           "twins",
    ("gs", "meg"):          "twins",
    # Gen 3 RS / Emerald
    ("rs", "rival"):        "wally",
    ("rs", "aqua_grunt"):   "team_aqua_grunt_m",
    ("rs", "magma_grunt"):  "team_magma_grunt_m",
    ("rs", "aqua_admin"):   "team_aqua_grunt_m",
    ("rs", "magma_admin"):  "team_magma_grunt_m",
    ("rs", "grunt"):        "team_aqua_grunt_m",
    ("rs", "grunt_weather_ins"): "team_magma_grunt_m",
    ("rs", "cooltrainer"):  "cooltrainer_m",
    ("rs", "swimmer"):      "swimmer_m",
    ("rs", "pokefan"):      "pok_fan_m",
    ("rs", "pokéfan"):      "pok_fan_m",
    ("rs", "pokemaniac"):   "pok_maniac",
    ("rs", "tate&liza"):    "tate_and_liza",
    ("rs", "pokemon_breeder"): "pok_mon_breeder_m",
    ("rs", "pokémon_breeder"): "pok_mon_breeder_m",
    ("rs", "pokemon_ranger"): "pok_mon_ranger_m",
    ("rs", "pokémon_ranger"): "pok_mon_ranger_m",
    ("rs", "pkmn_trainer"): "wally",
    ("rs", "gentlman"):     "gentleman",
    ("rs", "batle_girl"):   "battle_girl",
    ("rs", "old_couple"):   "old_couple",
    ("rs", "sr_and_jr"):    "sr_and_jr",
    ("rs", "interviewer"):  "interviewer",
    ("rs", "pokémaniac"):   "pok_maniac",
    ("rs", "swimmer_f"):    "swimmer_m",
    ("rs", "picknicker"):   "picnicker",
    ("rs", "gatekeeper"):   "gentleman",
    ("rs", "triathlete"):   "triathlete_runner_m",
    ("rs", "traithlete"):   "triathlete_runner_m",
    ("rs", "trialthete"):   "triathlete_runner_m",
    ("rs", "winstrate"):    "lady",
    ("rs", "team_magma_straggler"): "team_magma_grunt_m",
    ("rs", "youg_couple"):  "young_couple",
    ("rs", "sis_&_bro"):    "sis_and_bro",
    ("rs", "sr_&_jr"):      "sr_and_jr",
    # Gen 3 FRLG
    ("frlg", "rival"):       "cooltrainer_m",
    ("frlg", "rival_champ"): "cooltrainer_m",
    ("frlg", "surge"):       "lt_surge",
    ("frlg", "pokemaniac"):  "pok_maniac",
    ("frlg", "cooltrainer"): "cooltrainer_m",
    ("frlg", "cool_couple"): "cool_couple",
    ("frlg", "crush_kin"):   "crush_kin",
    ("frlg", "swimmer"):     "swimmer_m",
    ("frlg", "rocket_grunt"): "team_rocket_grunt_m",
    ("frlg", "grunt"):       "team_rocket_grunt_m",
    ("frlg", "gentlman"):    "gentleman",
    ("frlg", "pokefan"):     "pok_fan_m",
    ("frlg", "pokéfan"):     "pok_fan_m",
    ("frlg", "sis_and_bro"): "sis_and_bro",
    ("frlg", "picknicker"):  "picnicker",
    ("frlg", "swimmer_f"):   "swimmer_m",
    ("frlg", "saillor"):    "sailor",
    # Gen 4 DP / Plat
    ("dp", "rival"):        "barry",
    ("dp", "wake"):         "crasher_wake",
    ("dp", "surge"):        "lt_surge",
    ("dp", "cooltrainer"):  "ace_trainer_m",
    ("dp", "swimmer"):      "swimmer_m",
    ("dp", "grunt"):        "galactic_grunt_m",
    ("dp", "pokefan"):      "pok_fan_m",
    ("dp", "pokéfan"):      "pok_fan_m",
    ("dp", "poke_kid"):     "pok__kid",
    ("dp", "pokemon_breeder"): "pok_mon_breeder_m",
    ("dp", "pokemon_ranger"): "pok_mon_ranger_m",
    ("dp", "pokémon_breeder"): "pok_mon_breeder_m",
    ("dp", "pokémon_ranger"): "pok_mon_ranger_m",
    ("dp", "pokemon_trainer"): "ace_trainer_m",
    ("dp", "breeder"):      "pok_mon_breeder_m",
    ("dp", "mars_&_jupiter"): "mars",
    ("dp", "double_team"):  "double_team",
    ("dp", "belle_&_pa"):   "double_team",
    ("dp", "fisherma"):     "fisherman",
    ("dp", "picknicker"):   "picnicker",
    ("dp", "swimmer_f"):    "swimmer_m",
    ("dp", "policeman"):    "officer",
    ("dp", "cyclist"):      "cyclist_m",
    ("dp", "al"):           "double_team",
    ("dp", "ava"):          "young_couple",
    ("dp", "beth"):         "young_couple",
    ("dp", "emma"):         "young_couple",
    ("dp", "jo"):           "twins",
    ("dp", "mike"):         "young_couple",
    ("dp", "teri"):         "twins",
    ("dp", "ranger"):       "pok_mon_ranger_m",
    ("dp", "rancho"):       "rancher",
    ("dp", "sceintist"):    "scientist",
    # Gen 4 HGSS
    ("hgss", "rival"):       "silver",
    ("hgss", "pkmn_trainer_red"): "red",
    ("hgss", "surge"):       "lt_surge",
    ("hgss", "pokemaniac"):  "pok_maniac",
    ("hgss", "pokefan"):     "pok_fan_m",
    ("hgss", "pokéfan"):     "pok_fan_m",
    ("hgss", "cooltrainer"): "ace_trainer_m",
    ("hgss", "cool_trainer"): "ace_trainer_m",
    ("hgss", "swimmer"):     "swimmer_m",
    ("hgss", "rocket_grunt"): "rocket_grunt_m",
    ("hgss", "grunt"):       "rocket_grunt_m",
    ("hgss", "schoolboy"):   "school_kid_m",
    ("hgss", "school_kid"):  "school_kid_m",
    ("hgss", "blackbelt"):   "black_belt",
    ("hgss", "fire_breather"): "firebreather",
    ("hgss", "firebreather"): "firebreather",
    ("hgss", "burgular"):    "burglar",
    ("hgss", "border"):      "boarder",
    ("hgss", "birdkeeper"):  "bird_keeper",
    ("hgss", "archer"):      "rocket_grunt_m",
    ("hgss", "ariana"):      "rocket_grunt_m",
    ("hgss", "proton"):      "rocket_grunt_m",
    ("hgss", "petrel"):      "petrel",
    ("hgss", "picknicker"):  "picnicker",
    ("hgss", "amy"):         "twins",
    ("hgss", "clea"):        "twins",
    ("hgss", "day"):         "twins",
    ("hgss", "duff"):        "twins",
    ("hgss", "elan"):        "twins",
    ("hgss", "jo"):          "twins",
    ("hgss", "meg"):         "twins",
    ("hgss", "kay"):         "twins",
    ("hgss", "moe"):         "twins",
    ("hgss", "poke_maniac"): "pok_maniac",
    ("hgss", "pshycic"):    "psychic",
    ("hgss", "schhool_kid"): "school_kid_m",
    ("hgss", "pokemon_trainer"): "ace_trainer_m",
    ("hgss", "policeman"):  "officer",
    ("hgss", "swimmer_f"):   "swimmer_m",
    ("hgss", "fisher"):      "fisherman",
    ("hgss", "twins"):       "twins",
    ("hgss", "elder"):       "sage",
    ("hgss", "proton"):      "rocket_grunt_m",
    ("hgss", "surge"):       "lt_surge",
    # Gen 5 BW
    ("bw", "rival"):        "cheren",
    ("bw", "grunt"):        "plasma_grunt_m",
    ("bw", "pokéfan"):      "pok_fan_m",
    ("bw", "pokefan"):      "pok_fan_m",
    ("bw", "pokémon_breeder"): "pok_mon_breeder_m",
    ("bw", "pokémon_ranger"): "pok_mon_ranger_m",
    ("bw", "pokemon_breeder"): "pok_mon_breeder_m",
    ("bw", "pokemon_ranger"): "pok_mon_ranger_m",
    ("bw", "swimmer"):      "swimmer_m",
    ("bw", "swimmer_f"):    "swimmer_m",
    ("bw", "clerk"):        "clerk_m",
    ("bw", "backpacker"):   "backpacker_m",
    ("bw", "school_kid"):   "school_kid_m",
    ("bw", "cyclist"):      "cyclist_m",
    ("bw", "pok_fan"):      "pok_fan_m",
    ("bw", "breeder"):      "pok_mon_breeder_m",
    ("bw", "picknicker"):   "picnicker",
    ("bw", "cheren"):       "ace_trainer_m",
    ("bw", "houghneck"):    "roughneck",
    ("bw", "ranger"):       "pok_mon_ranger_m",
    ("bw", "psychic"):      "psychic",
    # Gen 5 B2W2
    ("b2w2", "rival"):       "hugh",
    ("b2w2", "grunt"):       "plasma_grunt_m",
    ("b2w2", "plasma_shadow"): "plasma_grunt_m",
    ("b2w2", "plasma_double"): "plasma_grunt_m",
    ("b2w2", "pokéfan"):     "pok_fan_m",
    ("b2w2", "pokefan"):     "pok_fan_m",
    ("b2w2", "pokémon_breeder"): "pok_mon_breeder_m",
    ("b2w2", "pokémon_ranger"): "pok_mon_ranger_m",
    ("b2w2", "pokemon_breeder"): "pok_mon_breeder_m",
    ("b2w2", "pokemon_ranger"): "pok_mon_ranger_m",
    ("b2w2", "swimmer"):     "swimmer_m",
    ("b2w2", "swimmer_f"):  "swimmer_m",
    ("b2w2", "clerk"):      "clerk_m",
    ("b2w2", "backpacker"): "backpacker_m",
    ("b2w2", "school_kid"): "school_kid_m",
    ("b2w2", "cyclist"):    "cyclist_m",
    ("b2w2", "pok_fan"):    "pok_fan_m",
    ("b2w2", "breeder"):    "pok_mon_breeder_m",
    ("b2w2", "picknicker"):  "picnicker",
    ("b2w2", "ranger"):      "pok_mon_ranger_m",
    ("b2w2", "pkmn_ranger"): "pok_mon_ranger_m",
    ("b2w2", "policeman"):   "officer",
    ("b2w2", "preeschooler"): "preschooler_m",
    ("b2w2", "parsol_lady"): "parasol_lady",
    ("b2w2", "motorcyclist"): "biker",
    ("b2w2", "gf"):          "gentleman",
    ("b2w2", "ghetsis"):     "plasma_grunt_m",
    ("b2w2", "guitarist"):   "guitarist",
    ("b2w2", "dancer"):      "dancer",
    ("b2w2", "ava"):         "twins",
    ("b2w2", "claude"):      "twins",
    ("b2w2", "rob"):         "twins",
    ("b2w2", "sola"):        "twins",
    ("b2w2", "stu"):         "twins",
}


def _build_available_sprites() -> set[str]:
    """Return a set of all sprite filenames (e.g. 'rg_brock.webp')."""
    if not SPRITES_DIR.exists():
        return set()
    return {f.name for f in SPRITES_DIR.iterdir() if f.suffix == ".webp"}


def _normalize_name(name: str) -> str:
    """Lowercase, strip trailing numbers/direction suffixes, normalise to underscore."""
    # Strip trailing number (e.g. "Bug Catcher 1" → "Bug Catcher")
    name = re.sub(r"\s+\d+$", "", name.strip())
    # Strip trailing "Double" suffix (e.g. "Grunt Double" → "Grunt")
    name = re.sub(r"\s+Double$", "", name)
    # Strip trailing (Double) suffix (e.g. "Ace Trainer Cora (Double)")
    name = re.sub(r"\s*\(Double\)$", "", name)
    # Strip trailing directional suffixes (e.g. "Channeler NW" → "Channeler")
    name = re.sub(r"\s+(?:N|S|E|W|NE|NW|SE|SW)$", "", name)
    # Strip "Space Tag" suffix (Emerald-specific)
    name = re.sub(r"\s+Space Tag$", "", name)
    # Strip gender symbols
    name = name.replace("\u2640", "").replace("\u2642", "").strip()
    # Lowercase, replace spaces/periods/dashes with underscore
    name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_")
    # Collapse double underscores from stripping
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _resolve_trainer_sprite(
    trainer_name: str,
    sprite_prefix: str,
    available: set[str],
) -> str:
    """
    Return the sprite path (relative to src/) for a trainer, or "" if none found.

    Tries multiple strategies in order:
    1. Full normalised name
    2. Full normalised name + _m (male variant)
    3. Last word only (handles "Leader Bugsy" → bugsy, "Elite Four Will" → will)
    4. All words except last (handles "Ace Trainer Allen" → ace_trainer)
    5. All words except last + _m
    6. Alias map
    """
    # For pair trainers like "Ace Trainer Jenn & Irene", use only the left half.
    if " & " in trainer_name:
        trainer_name = trainer_name.split(" & ")[0]
    elif " and " in trainer_name.lower():
        # Handle "Old Couple John and Jay" → "Old Couple John"
        trainer_name = re.split(r"\s+and\s+", trainer_name, flags=re.IGNORECASE)[0]

    norm = _normalize_name(trainer_name)

    # Check alias map first (highest priority for known edge cases).
    alias = _SPRITE_ALIASES.get((sprite_prefix, norm))
    if alias:
        candidate = f"{sprite_prefix}_{alias}.webp"
        if candidate in available:
            return f"data/sprites/{candidate}"

    # Strategy 1: exact normalised name.
    candidate = f"{sprite_prefix}_{norm}.webp"
    if candidate in available:
        return f"data/sprites/{candidate}"

    # Strategy 2: with _m suffix.
    candidate = f"{sprite_prefix}_{norm}_m.webp"
    if candidate in available:
        return f"data/sprites/{candidate}"

    # For multi-word names, try splitting.
    parts = norm.split("_")
    if len(parts) >= 2:
        # Strategy 3: last word only (for "Leader Bugsy" → "bugsy").
        last = parts[-1]
        # Check alias for just the last word too.
        alias = _SPRITE_ALIASES.get((sprite_prefix, last))
        if alias:
            candidate = f"{sprite_prefix}_{alias}.webp"
            if candidate in available:
                return f"data/sprites/{candidate}"

        candidate = f"{sprite_prefix}_{last}.webp"
        if candidate in available:
            return f"data/sprites/{candidate}"

        # Strategy 4: everything except last word (for "Ace Trainer Allen" → "ace_trainer").
        class_name = "_".join(parts[:-1])
        alias = _SPRITE_ALIASES.get((sprite_prefix, class_name))
        if alias:
            candidate = f"{sprite_prefix}_{alias}.webp"
            if candidate in available:
                return f"data/sprites/{candidate}"

        candidate = f"{sprite_prefix}_{class_name}.webp"
        if candidate in available:
            return f"data/sprites/{candidate}"

        # Strategy 5: class name + _m.
        candidate = f"{sprite_prefix}_{class_name}_m.webp"
        if candidate in available:
            return f"data/sprites/{candidate}"

    return ""


# ---------------------------------------------------------------------------
# IV / DV normalisation helpers
# ---------------------------------------------------------------------------
# The JSON files use two different formats:
#   Gen 1-2 (DVs):  {"hp": 8, "at": 9, "df": 8, "sl": 8, "sd": 8, "sp": 8}
#   Gen 3+  (IVs):  {"hp": 31, "at": 31, "df": 31, "sa": 31, "sd": 31, "sp": 31}
#
# calc._normalize_ivs mis-detects the Gen 3+ format because "at"/"df"/"sd"/"sp"
# overlap with DV_ALIASES keys.  We handle both formats explicitly here.

_DV_KEY_MAP = {
    "hp": "hp",
    "at": "attack",
    "df": "defense",
    "sl": "special_attack",
    "sd": "special_defense",
    "sp": "speed",
}

_IV_KEY_MAP = {
    "hp": "hp",
    "at": "attack",
    "df": "defense",
    "sa": "special_attack",
    "sd": "special_defense",
    "sp": "speed",
}


def _normalize_trainer_ivs(raw: dict, is_dv: bool) -> dict[str, int]:
    """
    Convert a raw DV/IV dict from the JSON into the normalised
    {stat_key: 0-31 IV value} dict expected by _calculate_stat.

    For DVs the value is clamped 0-15 then doubled (as calc.py does).
    For IVs the value is clamped 0-31.
    """
    key_map = _DV_KEY_MAP if is_dv else _IV_KEY_MAP
    normalised: dict[str, int] = {s: 0 for s in STAT_KEYS}

    for raw_key, value in raw.items():
        stat_key = key_map.get(raw_key)
        if stat_key is None:
            continue
        try:
            v = int(value)
        except (TypeError, ValueError):
            continue
        if is_dv:
            v = max(0, min(15, v)) * 2
        else:
            v = max(0, min(31, v))
        normalised[stat_key] = v

    return normalised


# ---------------------------------------------------------------------------
# DB helper queries
# ---------------------------------------------------------------------------

def _build_pokemon_map(db: Session) -> dict[str, AllPokemon]:
    """Return a lowercase name -> AllPokemon model map."""
    all_pokemon = db.query(AllPokemon).all()
    return {p.name.lower(): p for p in all_pokemon}


def _get_version_ids(db: Session, game_names: list[str]) -> list[int]:
    """Return version_ids for the given game names."""
    versions = (
        db.query(Version.version_id)
        .filter(func.lower(Version.version_name).in_([g.lower() for g in game_names]))
        .all()
    )
    return [v.version_id for v in versions]


def _get_route_candidates(db: Session, version_ids: list[int]) -> list[tuple[str, int]]:
    """Return (route_name, route_id) pairs for the given version_ids."""
    if not version_ids:
        return []
    routes = (
        db.query(Route.name, Route.id)
        .filter(Route.version_id.in_(version_ids))
        .all()
    )
    return [(r.name, r.id) for r in routes]


def _get_gym_leader_names(db: Session, game_names: list[str]) -> set[str]:
    """Return a set of lowercased gym leader names for the given game names."""
    gyms = (
        db.query(Gym.trainer_name)
        .filter(func.lower(Gym.game_name).in_([g.lower() for g in game_names]))
        .all()
    )
    return {g.trainer_name.lower() for g in gyms if g.trainer_name}



def _compute_pokemon_stats(
    poke_entry: dict,
    pokemon_map: dict[str, AllPokemon],
    is_dv: bool,
) -> dict | None:
    """
    Given a single pokemon entry from the JSON, look up base stats and compute
    true stats.  Returns a dict ready for the Trainer.pokemon JSON column, or
    None if the pokemon is not found in the AllPokemon table.
    """
    name = poke_entry["name"]
    level = poke_entry["level"]
    base = pokemon_map.get(name.lower())

    extra_fields = {
        "index": poke_entry.get("index"),
        "ability": poke_entry.get("ability"),
        "item": poke_entry.get("item"),
        "nature": poke_entry.get("nature"),
        "ivs": poke_entry.get("ivs"),
        "dvs": poke_entry.get("dvs"),
        "evs": poke_entry.get("evs"),
    }

    if base is None:
        print(f"  [WARN] Pokemon '{name}' not found in AllPokemon table — skipping stat calc")
        return {
            "name": name,
            "poke_id": None,
            "level": level,
            "types": poke_entry.get("types", []),
            "moves": poke_entry.get("moves", []),
            "stats": None,
            **extra_fields,
        }

    # Get the raw DV/IV dict from whichever key is present.
    raw_ivs = poke_entry.get("dvs") or poke_entry.get("ivs") or {}
    normalised_ivs = _normalize_trainer_ivs(raw_ivs, is_dv=is_dv)

    base_stats = {
        "hp": base.base_hp,
        "attack": base.base_attack,
        "defense": base.base_defense,
        "special_attack": base.base_special_attack,
        "special_defense": base.base_special_defense,
        "speed": base.base_speed,
    }

    stats: dict[str, int] = {}
    for stat_key in STAT_KEYS:
        stats[stat_key] = _calculate_stat(
            base_stats[stat_key],
            normalised_ivs[stat_key],
            level,
            nature_modifier=1.0,
            is_hp=(stat_key == "hp"),
            ev=0,
        )

    return {
        "name": name,
        "poke_id": base.poke_id,
        "level": level,
        "types": base.types or [],
        "moves": poke_entry.get("moves", []),
        "stats": stats,
        **extra_fields,
    }


def populate(db: Session) -> None:
    pokemon_map = _build_pokemon_map(db)
    if not pokemon_map:
        print("[ERROR] AllPokemon table is empty — run pokemon population first.")
        return

    print(f"Loaded {len(pokemon_map)} pokemon from AllPokemon table.")

    # Wipe existing Trainer rows for re-runs.
    deleted = db.query(Trainer).delete()
    db.commit()
    print(f"Cleared {deleted} existing Trainer rows.")

    global_battle_order = 0  # running counter across *all* files
    available_sprites = _build_available_sprites()
    print(f"Found {len(available_sprites)} sprite files on disk.")

    for rel_path, (game_names, generation) in FILE_MAP.items():
        json_path = DATA_DIR / rel_path
        if not json_path.exists():
            print(f"[SKIP] {rel_path} — file not found at {json_path}")
            continue

        print(f"\n--- Processing {rel_path} (games={game_names}, gen={generation}) ---")

        with open(json_path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        # Determine whether this gen uses DVs (Gen 1-2) or IVs (Gen 3+).
        is_dv = generation <= 2

        # Look up sprite prefix for this file (empty for Gen 6+).
        sprite_prefix = SPRITE_PREFIX_MAP.get(rel_path, "")

        # Fetch route candidates and gym leader names for this set of games.
        version_ids = _get_version_ids(db, game_names)
        route_candidates = _get_route_candidates(db, version_ids)
        gym_leader_names = _get_gym_leader_names(db, game_names)

        print(f"  version_ids={version_ids}, routes={len(route_candidates)}, gym_leaders={gym_leader_names}")

        # Phase 1: Build trainer records.
        trainer_records: list[dict] = []
        sprite_hits = 0
        sprite_misses = 0

        for entry in entries:
            global_battle_order += 1

            trainer_name = entry.get("trainer", "Unknown")
            location = entry.get("location") or ""
            starter = entry.get("starter")  # may be None

            # Resolve sprite from trainer name + game prefix.
            if sprite_prefix:
                sprite = _resolve_trainer_sprite(trainer_name, sprite_prefix, available_sprites)
                if sprite:
                    sprite_hits += 1
                else:
                    sprite_misses += 1
                    print(f"  [MISS] No sprite for: {trainer_name}")
            else:
                sprite = ""

            # Compute pokemon entries with true stats.
            pokemon_out: list[dict] = []
            levels: list[int] = []

            for poke in entry.get("pokemon", []):
                poke_data = _compute_pokemon_stats(poke, pokemon_map, is_dv)
                if poke_data is not None:
                    pokemon_out.append(poke_data)
                    levels.append(poke["level"])

            avg_level = sum(levels) / len(levels) if levels else 0.0

            # Fuzzy-match location to a route.
            route_id = None
            if location and route_candidates:
                route_id = fuzzy_match_route(location, route_candidates)

            # Classify importance.
            importance_reason, is_important = classify_importance(
                trainer_name, location, gym_leader_names,
                game_names=tuple(game_names),
            )

            trainer_records.append({
                "generation": generation,
                "game_names": game_names,
                "trainer_name": trainer_name,
                "trainer_image": sprite,
                "location": location,
                "route_id": route_id,
                "is_important": is_important,
                "importance_reason": importance_reason,
                "starter_filter": starter,
                "battle_order": global_battle_order,
                "pokemon": pokemon_out,
                "avg_level": avg_level,
            })

        if sprite_prefix:
            total = sprite_hits + sprite_misses
            pct = (sprite_hits / total * 100) if total else 0
            print(f"  Sprites: {sprite_hits}/{total} matched ({pct:.0f}%)")

        # Phase 2: Detect level outliers among non-important trainers.
        non_important = [
            {"battle_order": r["battle_order"], "avg_level": r["avg_level"]}
            for r in trainer_records
            if not r["is_important"]
        ]
        outlier_orders = detect_level_outliers(non_important)

        for rec in trainer_records:
            if rec["battle_order"] in outlier_orders and not rec["is_important"]:
                rec["is_important"] = True
                rec["importance_reason"] = "level_outlier"

        # Phase 3: Insert Trainer rows.
        inserted = 0
        for rec in trainer_records:
            trainer = Trainer(
                generation=rec["generation"],
                game_names=rec["game_names"],
                trainer_name=rec["trainer_name"],
                trainer_image=rec["trainer_image"],
                location=rec["location"],
                route_id=rec["route_id"],
                is_important=rec["is_important"],
                importance_reason=rec["importance_reason"],
                starter_filter=rec["starter_filter"],
                battle_order=rec["battle_order"],
                pokemon=rec["pokemon"],
            )
            db.add(trainer)
            inserted += 1

        db.commit()
        print(f"  Inserted {inserted} trainers ({sum(1 for r in trainer_records if r['is_important'])} important).")

    print("\nDone.")



if __name__ == "__main__":
    db = SessionLocal()
    try:
        populate(db)
    except Exception as e:
        db.rollback()
        print(f"\n[FATAL] {e}", file=sys.stderr)
        raise
    finally:
        db.close()
