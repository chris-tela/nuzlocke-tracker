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


# ---------------------------------------------------------------------------
# Stat computation for a single trainer pokemon
# ---------------------------------------------------------------------------

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

    if base is None:
        print(f"  [WARN] Pokemon '{name}' not found in AllPokemon table — skipping stat calc")
        return {
            "name": name,
            "level": level,
            "moves": poke_entry.get("moves", []),
            "stats": None,
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
        "level": level,
        "moves": poke_entry.get("moves", []),
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# Main population logic
# ---------------------------------------------------------------------------

def populate(db: Session) -> None:
    pokemon_map = _build_pokemon_map(db)
    if not pokemon_map:
        print("[ERROR] AllPokemon table is empty — run pokemon population first.")
        return

    print(f"Loaded {len(pokemon_map)} pokemon from AllPokemon table.")

    # Wipe existing Trainer rows for idempotent re-runs.
    deleted = db.query(Trainer).delete()
    db.commit()
    print(f"Cleared {deleted} existing Trainer rows.")

    global_battle_order = 0  # running counter across *all* files

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

        # Fetch route candidates and gym leader names for this set of games.
        version_ids = _get_version_ids(db, game_names)
        route_candidates = _get_route_candidates(db, version_ids)
        gym_leader_names = _get_gym_leader_names(db, game_names)

        print(f"  version_ids={version_ids}, routes={len(route_candidates)}, gym_leaders={gym_leader_names}")

        # Phase 1: Build trainer records.
        trainer_records: list[dict] = []

        for entry in entries:
            global_battle_order += 1

            trainer_name = entry.get("trainer", "Unknown")
            location = entry.get("location") or ""
            starter = entry.get("starter")  # may be None
            sprite = entry.get("sprite") or ""

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
                trainer_name, location, gym_leader_names
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
