# Trainer Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Trainer table populated from Gen JSON data with precomputed stats, expose via API, display in a new Trainers page and on Route cards.

**Architecture:** New `Trainer` SQLAlchemy model populated by a `populate_trainers.py` script that reads `src/data/Gen*/*.json`, computes true stats via `calc.py`, fuzzy-matches locations to Route DB records, and flags important trainers. Three new API endpoints serve trainer data. Frontend adds a TrainersPage with Key Battles + route-grouped accordion, a TrainerCard component, and route page integration.

**Tech Stack:** Python/FastAPI/SQLAlchemy (backend), TypeScript/React/React Query (frontend), existing `calc.py` stat formulas.

**Design doc:** `docs/plans/2026-02-12-trainer-feature-design.md`

---

### Task 1: Add Trainer model to database

**Files:**
- Modify: `src/backend/db/models.py`

**Step 1: Add the Trainer model**

Add after the `Gym` class in `src/backend/db/models.py`:

```python
class Trainer(Base):
    __tablename__ = "trainer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation = Column(Integer, nullable=False)
    game_names = Column(ARRAY(String), nullable=False)
    trainer_name = Column(String, nullable=False)
    trainer_image = Column(String, nullable=False)
    location = Column(String, nullable=False)
    route_id = Column(Integer, ForeignKey("route.id"), nullable=True)
    is_important = Column(Boolean, nullable=False, default=False)
    importance_reason = Column(String, nullable=True)
    starter_filter = Column(String, nullable=True)
    battle_order = Column(Integer, nullable=False)
    pokemon = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    route = relationship("Route")
```

**Step 2: Create the table in the database**

Run from `src/backend/`:
```bash
python -c "
from db.database import engine, Base
from db.models import Trainer
Trainer.__table__.create(engine, checkfirst=True)
print('Trainer table created')
"
```

Expected: `Trainer table created` (no errors)

**Step 3: Commit**

```bash
git add src/backend/db/models.py
git commit -m "feat: add Trainer database model"
```

---

### Task 2: Write fuzzy route matching utility

**Files:**
- Create: `src/backend/route_matching.py`
- Create: `src/backend/tests/test_route_matching.py`

**Step 1: Write the failing test**

Create `src/backend/tests/test_route_matching.py`:

```python
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from route_matching import normalize_name, jaccard_similarity, fuzzy_match_route


def test_normalize_name_strips_punctuation_and_lowercases():
    assert normalize_name("Pewter City") == "pewter city"
    assert normalize_name("Mt. Moon") == "mt moon"
    assert normalize_name("Professor Oak's Lab") == "professor oaks lab"
    assert normalize_name("Route-3") == "route3"


def test_jaccard_similarity_exact_match():
    assert jaccard_similarity("pewter city", "pewter city") == 1.0


def test_jaccard_similarity_no_overlap():
    assert jaccard_similarity("pewter city", "cerulean cave") == 0.0


def test_jaccard_similarity_partial_overlap():
    score = jaccard_similarity("viridian city", "viridian forest")
    assert 0.3 < score < 0.7  # "viridian" overlaps, but city/forest differ


def test_fuzzy_match_route_exact():
    routes = [("pewter-city", 1), ("cerulean-city", 2)]
    assert fuzzy_match_route("Pewter City", routes) == 1


def test_fuzzy_match_route_substring_fallback():
    routes = [("professor-oaks-lab", 1), ("pallet-town", 2)]
    assert fuzzy_match_route("Lab", routes) == 1


def test_fuzzy_match_route_no_match():
    routes = [("pewter-city", 1), ("cerulean-city", 2)]
    assert fuzzy_match_route("Unknown Place", routes) is None
```

**Step 2: Run test to verify it fails**

Run: `cd src/backend && python -m pytest tests/test_route_matching.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'route_matching'`

**Step 3: Write the implementation**

Create `src/backend/route_matching.py`:

```python
import re


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation (except spaces), collapse whitespace."""
    result = name.lower()
    result = re.sub(r"['\.\-]", "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two normalized strings."""
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a and not tokens_b:
        return 1.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def fuzzy_match_route(
    trainer_location: str,
    route_candidates: list[tuple[str, int]],
    threshold: float = 0.8,
) -> int | None:
    """
    Match a trainer location string to a route ID.

    Args:
        trainer_location: Raw location string from trainer JSON (e.g., "Pewter City")
        route_candidates: List of (route_name, route_id) tuples from the DB
        threshold: Minimum Jaccard score for a match (default 0.8)

    Returns:
        Matched route_id, or None if no match found.
    """
    norm_location = normalize_name(trainer_location)

    # Pass 1: Jaccard similarity >= threshold
    best_score = 0.0
    best_id = None
    for route_name, route_id in route_candidates:
        norm_route = normalize_name(route_name)
        score = jaccard_similarity(norm_location, norm_route)
        if score >= threshold and score > best_score:
            best_score = score
            best_id = route_id

    if best_id is not None:
        return best_id

    # Pass 2: Substring containment fallback
    for route_name, route_id in route_candidates:
        norm_route = normalize_name(route_name)
        if norm_location in norm_route or norm_route in norm_location:
            return route_id

    return None
```

**Step 4: Run tests to verify they pass**

Run: `cd src/backend && python -m pytest tests/test_route_matching.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add src/backend/route_matching.py src/backend/tests/test_route_matching.py
git commit -m "feat: add fuzzy route matching utility with tests"
```

---

### Task 3: Write important trainer detection

**Files:**
- Create: `src/backend/trainer_importance.py`
- Create: `src/backend/tests/test_trainer_importance.py`

**Step 1: Write the failing test**

Create `src/backend/tests/test_trainer_importance.py`:

```python
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from trainer_importance import classify_importance, detect_level_outliers


def test_classify_rival():
    assert classify_importance("Rival 1", "Lab", set()) == ("rival", True)
    assert classify_importance("Rival 5", "R22", set()) == ("rival", True)


def test_classify_gym_leader_by_name():
    gym_names = {"brock", "misty", "lt. surge"}
    assert classify_importance("Brock", "Pewter Gym", gym_names) == ("gym_leader", True)


def test_classify_champion():
    assert classify_importance("Champion", "Champion", set()) == ("champion", True)


def test_classify_elite_four():
    assert classify_importance("Lorelei", "Elite Four", set()) == ("elite_four", True)


def test_classify_evil_team():
    assert classify_importance("Team Rocket Boss Giovanni", "Silph Co", set()) == ("evil_team_leader", True)
    assert classify_importance("Admin Mars", "Galactic HQ", set()) == ("evil_team_leader", True)


def test_classify_normal_trainer():
    result = classify_importance("Bug Catcher 1", "R3", set())
    assert result == (None, False)


def test_detect_level_outliers():
    # Trainers: indices 0-6, trainer at index 3 has avg level 30 vs ~15 for others
    trainer_levels = [
        {"battle_order": 0, "avg_level": 14},
        {"battle_order": 1, "avg_level": 15},
        {"battle_order": 2, "avg_level": 16},
        {"battle_order": 3, "avg_level": 30},  # outlier: 30 > 15 * 1.2
        {"battle_order": 4, "avg_level": 15},
        {"battle_order": 5, "avg_level": 16},
        {"battle_order": 6, "avg_level": 14},
    ]
    outlier_indices = detect_level_outliers(trainer_levels, window=3)
    assert 3 in outlier_indices


def test_detect_level_outliers_no_outlier():
    trainer_levels = [
        {"battle_order": i, "avg_level": 15 + i}
        for i in range(7)
    ]
    outlier_indices = detect_level_outliers(trainer_levels, window=3)
    assert len(outlier_indices) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd src/backend && python -m pytest tests/test_trainer_importance.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'trainer_importance'`

**Step 3: Write the implementation**

Create `src/backend/trainer_importance.py`:

```python
import statistics


RIVAL_KEYWORDS = ["rival"]

CHAMPION_KEYWORDS = ["champion"]

ELITE_FOUR_LOCATIONS = ["elite four"]

EVIL_TEAM_NAMES = [
    "rocket", "magma", "aqua", "galactic", "plasma",
    "flare", "skull", "yell", "star",
]

EVIL_ROLE_KEYWORDS = ["boss", "admin", "leader"]


def classify_importance(
    trainer_name: str,
    location: str,
    gym_leader_names: set[str],
) -> tuple[str | None, bool]:
    """
    Classify a trainer's importance based on role.

    Args:
        trainer_name: The trainer's name from JSON
        location: The trainer's location from JSON
        gym_leader_names: Set of known gym leader names (lowercased) from Gym table

    Returns:
        (importance_reason, is_important) tuple
    """
    name_lower = trainer_name.lower()
    location_lower = location.lower()

    # Rival
    if any(kw in name_lower for kw in RIVAL_KEYWORDS):
        return ("rival", True)

    # Gym leader (cross-reference Gym table names)
    if gym_leader_names and name_lower in gym_leader_names:
        return ("gym_leader", True)

    # Champion
    if any(kw in name_lower for kw in CHAMPION_KEYWORDS) or any(
        kw in location_lower for kw in CHAMPION_KEYWORDS
    ):
        return ("champion", True)

    # Elite Four
    if any(kw in location_lower for kw in ELITE_FOUR_LOCATIONS):
        return ("elite_four", True)

    # Evil team leader/admin
    has_team_name = any(team in name_lower for team in EVIL_TEAM_NAMES)
    has_role = any(role in name_lower for role in EVIL_ROLE_KEYWORDS)
    if has_team_name or has_role:
        return ("evil_team_leader", True)

    return (None, False)


def detect_level_outliers(
    trainer_levels: list[dict],
    window: int = 3,
    threshold: float = 1.2,
) -> set[int]:
    """
    Detect trainers whose average pokemon level is an outlier
    compared to nearby trainers (±window in battle_order).

    Args:
        trainer_levels: List of {"battle_order": int, "avg_level": float}
        window: Number of neighbors on each side to compare
        threshold: Multiplier — if avg_level > median * threshold, it's an outlier

    Returns:
        Set of battle_order values that are outliers
    """
    outliers = set()
    sorted_trainers = sorted(trainer_levels, key=lambda t: t["battle_order"])

    for i, trainer in enumerate(sorted_trainers):
        start = max(0, i - window)
        end = min(len(sorted_trainers), i + window + 1)
        neighbors = [
            sorted_trainers[j]["avg_level"]
            for j in range(start, end)
            if j != i
        ]
        if not neighbors:
            continue
        median_level = statistics.median(neighbors)
        if median_level > 0 and trainer["avg_level"] > median_level * threshold:
            outliers.add(trainer["battle_order"])

    return outliers
```

**Step 4: Run tests to verify they pass**

Run: `cd src/backend && python -m pytest tests/test_trainer_importance.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add src/backend/trainer_importance.py src/backend/tests/test_trainer_importance.py
git commit -m "feat: add trainer importance classification with tests"
```

---

### Task 4: Write populate_trainers.py script

**Files:**
- Create: `src/backend/populate_trainers.py`

This script reads all `src/data/Gen*/*.json` files, computes true stats via `calc.py`, runs fuzzy route matching, runs importance classification, and inserts into the `Trainer` table.

**Step 1: Write the population script**

Create `src/backend/populate_trainers.py`:

```python
"""
Populate the Trainer table from Gen JSON data files.
Computes true stats, fuzzy-matches routes, and classifies importance.

Usage: python populate_trainers.py
"""

import os
import sys
import json
import statistics

from sqlalchemy.orm import Session
from db.database import engine, SessionLocal
from db.models import Trainer, AllPokemon, Route, Gym, Base
from calc import _normalize_ivs, _calculate_stat
from route_matching import fuzzy_match_route
from trainer_importance import classify_importance, detect_level_outliers

# Map JSON file -> (game_names, generation)
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


def compute_pokemon_stats(poke_data: dict, all_pokemon_map: dict) -> dict | None:
    """Compute true stats for a trainer's pokemon using calc.py formulas."""
    name = poke_data["name"].lower()
    level = poke_data["level"]
    dvs = poke_data.get("dvs", {})

    # Look up base stats from AllPokemon
    base = all_pokemon_map.get(name)
    if base is None:
        return None

    # Normalize DVs/IVs using calc.py
    try:
        normalized_ivs = _normalize_ivs(dvs if dvs else {"hp": 0, "at": 0, "df": 0, "sl": 0, "sd": 0, "sp": 0})
    except ValueError:
        normalized_ivs = {k: 0 for k in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}

    base_stats = {
        "hp": base.base_hp,
        "attack": base.base_attack,
        "defense": base.base_defense,
        "special_attack": base.base_special_attack,
        "special_defense": base.base_special_defense,
        "speed": base.base_speed,
    }

    stats = {}
    for stat_key, base_val in base_stats.items():
        stats[stat_key] = _calculate_stat(
            base_val,
            normalized_ivs[stat_key],
            level,
            nature_modifier=1.0,  # Trainer pokemon have no nature effect
            is_hp=(stat_key == "hp"),
            ev=0,
        )

    return stats


def build_pokemon_entry(poke_data: dict, all_pokemon_map: dict) -> dict:
    """Build a pokemon entry with precomputed stats for the Trainer.pokemon JSON."""
    name = poke_data["name"]
    base = all_pokemon_map.get(name.lower())
    poke_id = base.poke_id if base else None

    stats = compute_pokemon_stats(poke_data, all_pokemon_map)

    return {
        "name": name,
        "poke_id": poke_id,
        "level": poke_data["level"],
        "moves": poke_data.get("moves", []),
        "stats": stats,
    }


def get_route_candidates(db: Session, game_names: list[str]) -> list[tuple[str, int]]:
    """Get (route_name, route_id) pairs for fuzzy matching."""
    from sqlalchemy import func
    from db.models import Version

    # Find version_ids for these game names
    versions = db.query(Version).filter(
        func.lower(Version.version_name).in_([g.lower() for g in game_names])
    ).all()

    version_ids = [v.version_id for v in versions]
    if not version_ids:
        return []

    routes = db.query(Route).filter(Route.version_id.in_(version_ids)).all()
    return [(r.name, r.id) for r in routes]


def get_gym_leader_names(db: Session, game_names: list[str]) -> set[str]:
    """Get lowercased gym leader names for importance classification."""
    gyms = db.query(Gym).filter(
        Gym.game_name.in_([g.lower() for g in game_names])
    ).all()
    return {g.trainer_name.lower() for g in gyms if g.trainer_name}


def populate():
    """Main population function."""
    db = SessionLocal()

    try:
        # Load all pokemon into a name->model map for stat lookups
        all_pokemon = db.query(AllPokemon).all()
        all_pokemon_map = {p.name.lower(): p for p in all_pokemon}
        print(f"Loaded {len(all_pokemon_map)} pokemon base stats")

        # Clear existing trainer data
        db.query(Trainer).delete()
        db.commit()
        print("Cleared existing trainer data")

        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

        for json_path, (game_names, generation) in FILE_MAP.items():
            file_path = os.path.join(data_dir, json_path)
            if not os.path.exists(file_path):
                print(f"WARNING: {file_path} not found, skipping")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                trainers_json = json.load(f)

            print(f"\nProcessing {json_path} ({len(trainers_json)} entries, games={game_names})")

            # Get route candidates and gym leader names for this game set
            route_candidates = get_route_candidates(db, game_names)
            gym_leader_names = get_gym_leader_names(db, game_names)

            # Phase 1: Build trainer records with stats and route matching
            trainer_records = []
            for idx, entry in enumerate(trainers_json):
                pokemon_entries = [
                    build_pokemon_entry(p, all_pokemon_map)
                    for p in entry.get("pokemon", [])
                ]

                # Fuzzy match route
                route_id = fuzzy_match_route(entry.get("location", ""), route_candidates)

                # Role-based importance
                reason, is_important = classify_importance(
                    entry.get("trainer", ""),
                    entry.get("location", ""),
                    gym_leader_names,
                )

                # Compute avg level for outlier detection
                levels = [p["level"] for p in entry.get("pokemon", []) if "level" in p]
                avg_level = statistics.mean(levels) if levels else 0

                trainer_records.append({
                    "generation": generation,
                    "game_names": game_names,
                    "trainer_name": entry.get("trainer", "Unknown"),
                    "trainer_image": entry.get("sprite", ""),
                    "location": entry.get("location", ""),
                    "route_id": route_id,
                    "is_important": is_important,
                    "importance_reason": reason,
                    "starter_filter": entry.get("starter"),  # None if null
                    "battle_order": idx,
                    "pokemon": pokemon_entries,
                    "avg_level": avg_level,
                })

            # Phase 2: Level outlier detection for non-important trainers
            non_important = [
                {"battle_order": t["battle_order"], "avg_level": t["avg_level"]}
                for t in trainer_records
                if not t["is_important"]
            ]
            outlier_orders = detect_level_outliers(non_important)

            for record in trainer_records:
                if not record["is_important"] and record["battle_order"] in outlier_orders:
                    record["is_important"] = True
                    record["importance_reason"] = "level_outlier"

            # Phase 3: Insert into DB
            for record in trainer_records:
                trainer = Trainer(
                    generation=record["generation"],
                    game_names=record["game_names"],
                    trainer_name=record["trainer_name"],
                    trainer_image=record["trainer_image"],
                    location=record["location"],
                    route_id=record["route_id"],
                    is_important=record["is_important"],
                    importance_reason=record["importance_reason"],
                    starter_filter=record["starter_filter"],
                    battle_order=record["battle_order"],
                    pokemon=record["pokemon"],
                )
                db.add(trainer)

            db.commit()
            print(f"  Inserted {len(trainer_records)} trainers")
            important_count = sum(1 for t in trainer_records if t["is_important"])
            matched_count = sum(1 for t in trainer_records if t["route_id"] is not None)
            print(f"  Important: {important_count}, Route-matched: {matched_count}/{len(trainer_records)}")

        print("\nPopulation complete!")
    finally:
        db.close()


if __name__ == "__main__":
    populate()
```

**Step 2: Run the population script**

Run from `src/backend/`:
```bash
python populate_trainers.py
```

Expected: Output showing each Gen file processed with trainer counts, importance counts, and route match counts. No errors.

**Step 3: Verify data in DB**

```bash
python -c "
from db.database import SessionLocal
from db.models import Trainer
db = SessionLocal()
total = db.query(Trainer).count()
important = db.query(Trainer).filter(Trainer.is_important == True).count()
matched = db.query(Trainer).filter(Trainer.route_id != None).count()
print(f'Total trainers: {total}')
print(f'Important: {important}')
print(f'Route-matched: {matched}')
sample = db.query(Trainer).filter(Trainer.is_important == True).first()
if sample:
    print(f'Sample: {sample.trainer_name} @ {sample.location} ({sample.importance_reason})')
    print(f'  Pokemon: {[p[\"name\"] + \" Lv.\" + str(p[\"level\"]) for p in sample.pokemon]}')
    if sample.pokemon and sample.pokemon[0].get('stats'):
        print(f'  Stats: {sample.pokemon[0][\"stats\"]}')
db.close()
"
```

Expected: Counts printed, sample trainer with computed stats visible.

**Step 4: Commit**

```bash
git add src/backend/populate_trainers.py
git commit -m "feat: add trainer population script with stat computation"
```

---

### Task 5: Add Pydantic schemas for trainer responses

**Files:**
- Modify: `src/backend/api/schemas.py`

**Step 1: Add trainer schemas**

Add at the end of `src/backend/api/schemas.py`, before the authentication schemas section:

```python
# Trainer Schemas
class TrainerPokemonStats(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

class TrainerPokemon(BaseModel):
    name: str
    poke_id: Optional[int] = None
    level: int
    moves: List[str] = []
    stats: Optional[TrainerPokemonStats] = None

class TrainerResponse(BaseModel):
    id: int
    generation: int
    game_names: List[str]
    trainer_name: str
    trainer_image: str
    location: str
    route_id: Optional[int] = None
    is_important: bool
    importance_reason: Optional[str] = None
    starter_filter: Optional[str] = None
    battle_order: int
    pokemon: List[TrainerPokemon]

    class Config:
        from_attributes = True
```

**Step 2: Commit**

```bash
git add src/backend/api/schemas.py
git commit -m "feat: add Pydantic schemas for trainer API responses"
```

---

### Task 6: Add trainer API router

**Files:**
- Create: `src/backend/api/routers/trainers.py`
- Modify: `src/backend/api/main.py`

**Step 1: Create the trainers router**

Create `src/backend/api/routers/trainers.py`:

```python
"""
Trainer data router.
Serves precomputed trainer data from the Trainer table.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from ...db import models
from ..dependencies import get_db
from ..schemas import TrainerResponse

router = APIRouter()


@router.get("/{game_name}", response_model=list[TrainerResponse])
async def get_trainers_by_game(
    game_name: str,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all trainers for a game, ordered by battle_order."""
    query = db.query(models.Trainer).filter(
        models.Trainer.game_names.any(game_name.lower())
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers


@router.get("/{game_name}/important", response_model=list[TrainerResponse])
async def get_important_trainers(
    game_name: str,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get only important trainers for a game."""
    query = db.query(models.Trainer).filter(
        models.Trainer.game_names.any(game_name.lower()),
        models.Trainer.is_important == True,  # noqa: E712
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers


@router.get("/by-route/{route_id}", response_model=list[TrainerResponse])
async def get_trainers_by_route(
    route_id: int,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all trainers matched to a specific route."""
    query = db.query(models.Trainer).filter(
        models.Trainer.route_id == route_id
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers
```

**Step 2: Register the router in main.py**

In `src/backend/api/main.py`, add the import:

```python
from .routers import auth, users, game_files, pokemon, routes, gyms, versions, trainers
```

And add the router registration after the versions router:

```python
app.include_router(trainers.router, prefix="/api/trainers", tags=["trainers"])
```

**Step 3: Test the API manually**

Start the server and test:
```bash
# From src/backend/
python -c "import uvicorn; uvicorn.run('api.main:app', host='0.0.0.0', port=8000)"
```

In another terminal:
```bash
curl http://localhost:8000/api/trainers/red?starter=Bulbasaur | python -m json.tool | head -30
curl http://localhost:8000/api/trainers/red/important | python -m json.tool | head -30
```

Expected: JSON arrays of trainer objects with pokemon stats.

**Step 4: Commit**

```bash
git add src/backend/api/routers/trainers.py src/backend/api/main.py
git commit -m "feat: add trainer API endpoints"
```

---

### Task 7: Add frontend types and service layer

**Files:**
- Create: `src/frontend/src/types/trainer.ts`
- Modify: `src/frontend/src/types/index.ts`
- Create: `src/frontend/src/services/trainerService.ts`
- Create: `src/frontend/src/hooks/useTrainers.ts`
- Modify: `src/frontend/src/hooks/queryKeys.ts`

**Step 1: Create TypeScript types**

Create `src/frontend/src/types/trainer.ts`:

```typescript
export interface TrainerPokemonStats {
  hp: number;
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
}

export interface TrainerPokemon {
  name: string;
  poke_id: number | null;
  level: number;
  moves: string[];
  stats: TrainerPokemonStats | null;
}

export interface Trainer {
  id: number;
  generation: number;
  game_names: string[];
  trainer_name: string;
  trainer_image: string;
  location: string;
  route_id: number | null;
  is_important: boolean;
  importance_reason: string | null;
  starter_filter: string | null;
  battle_order: number;
  pokemon: TrainerPokemon[];
}
```

**Step 2: Export from types index**

Add to `src/frontend/src/types/index.ts`:

```typescript
export * from './trainer';
```

**Step 3: Create trainer service**

Create `src/frontend/src/services/trainerService.ts`:

```typescript
import { apiHelpers } from './api';
import type { Trainer } from '../types/trainer';

export const getTrainersByGame = async (
  gameName: string,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(`/api/trainers/${encodeURIComponent(gameName)}${params}`);
};

export const getImportantTrainers = async (
  gameName: string,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(
    `/api/trainers/${encodeURIComponent(gameName)}/important${params}`
  );
};

export const getTrainersByRoute = async (
  routeId: number,
  starter?: string
): Promise<Trainer[]> => {
  const params = starter ? `?starter=${encodeURIComponent(starter)}` : '';
  return await apiHelpers.get<Trainer[]>(`/api/trainers/by-route/${routeId}${params}`);
};
```

**Step 4: Add query keys**

Add to `src/frontend/src/hooks/queryKeys.ts` inside the `queryKeys` object:

```typescript
  // Trainer queries
  trainers: (gameName: string, starter?: string) =>
    ['trainers', gameName, starter ?? 'all'] as const,
  importantTrainers: (gameName: string, starter?: string) =>
    ['trainers', gameName, 'important', starter ?? 'all'] as const,
  trainersByRoute: (routeId: number, starter?: string) =>
    ['trainers', 'route', routeId, starter ?? 'all'] as const,
```

**Step 5: Create hooks**

Create `src/frontend/src/hooks/useTrainers.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import {
  getTrainersByGame,
  getImportantTrainers,
  getTrainersByRoute,
} from '../services/trainerService';
import { queryKeys } from './queryKeys';

export const useTrainersByGame = (gameName: string | null, starter?: string) => {
  return useQuery({
    queryKey: gameName
      ? queryKeys.trainers(gameName, starter)
      : ['trainers', 'disabled'],
    queryFn: () => getTrainersByGame(gameName!, starter),
    enabled: !!gameName,
  });
};

export const useImportantTrainers = (gameName: string | null, starter?: string) => {
  return useQuery({
    queryKey: gameName
      ? queryKeys.importantTrainers(gameName, starter)
      : ['trainers', 'important', 'disabled'],
    queryFn: () => getImportantTrainers(gameName!, starter),
    enabled: !!gameName,
  });
};

export const useTrainersByRoute = (routeId: number | null, starter?: string) => {
  return useQuery({
    queryKey: routeId != null
      ? queryKeys.trainersByRoute(routeId, starter)
      : ['trainers', 'route', 'disabled'],
    queryFn: () => getTrainersByRoute(routeId!, starter),
    enabled: routeId != null,
  });
};
```

**Step 6: Commit**

```bash
git add src/frontend/src/types/trainer.ts src/frontend/src/types/index.ts src/frontend/src/services/trainerService.ts src/frontend/src/hooks/useTrainers.ts src/frontend/src/hooks/queryKeys.ts
git commit -m "feat: add frontend trainer types, service, and hooks"
```

---

### Task 8: Create TrainerCard component

**Files:**
- Create: `src/frontend/src/components/TrainerCard.tsx`

**Step 1: Build the TrainerCard component**

Create `src/frontend/src/components/TrainerCard.tsx`:

```typescript
import { useState } from 'react';
import type { Trainer, TrainerPokemon } from '../types/trainer';

const STAT_LABELS: Record<string, string> = {
  hp: 'HP',
  attack: 'Atk',
  defense: 'Def',
  special_attack: 'SpA',
  special_defense: 'SpD',
  speed: 'Spe',
};

const STAT_MAX = 255; // Reasonable max for stat bar scaling

const IMPORTANCE_BADGES: Record<string, { label: string; color: string }> = {
  rival: { label: 'Rival', color: '#E74C3C' },
  gym_leader: { label: 'Gym Leader', color: '#3498DB' },
  elite_four: { label: 'Elite Four', color: '#9B59B6' },
  champion: { label: 'Champion', color: '#F39C12' },
  evil_team_leader: { label: 'Evil Team', color: '#2C3E50' },
  level_outlier: { label: 'Tough Battle', color: '#E67E22' },
};

function PokemonStatBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min((value / STAT_MAX) * 100, 100);
  const color =
    value >= 100 ? '#22C55E' : value >= 60 ? '#3B82F6' : value >= 30 ? '#F59E0B' : '#EF4444';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
      <span style={{ width: '28px', textAlign: 'right', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
        {label}
      </span>
      <span style={{ width: '30px', textAlign: 'right', fontWeight: 600 }}>{value}</span>
      <div
        style={{
          flex: 1,
          height: '6px',
          backgroundColor: 'var(--color-border)',
          borderRadius: '3px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            backgroundColor: color,
            borderRadius: '3px',
            transition: 'width 300ms ease',
          }}
        />
      </div>
    </div>
  );
}

function PokemonEntry({ poke, apiBaseUrl }: { poke: TrainerPokemon; apiBaseUrl: string }) {
  const [expanded, setExpanded] = useState(false);
  const spriteUrl = poke.poke_id
    ? `${apiBaseUrl}/assets/sprites/${poke.poke_id}.webp`
    : '';

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '8px',
        borderRadius: '8px',
        border: '1px solid var(--color-border)',
        backgroundColor: expanded ? 'var(--color-bg-light)' : 'transparent',
        cursor: 'pointer',
        minWidth: '100px',
        transition: 'background-color 150ms ease',
      }}
    >
      {spriteUrl && (
        <img
          src={spriteUrl}
          alt={poke.name}
          loading="lazy"
          style={{ width: '48px', height: '48px', imageRendering: 'pixelated' }}
        />
      )}
      <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>{poke.name}</span>
      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
        Lv. {poke.level}
      </span>

      {expanded && poke.stats && (
        <div style={{ width: '100%', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {Object.entries(STAT_LABELS).map(([key, label]) => (
            <PokemonStatBar
              key={key}
              label={label}
              value={(poke.stats as Record<string, number>)[key] ?? 0}
            />
          ))}
          {poke.moves.length > 0 && (
            <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              {poke.moves.join(' / ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface TrainerCardProps {
  trainer: Trainer;
  highlight?: boolean;
}

export function TrainerCard({ trainer, highlight }: TrainerCardProps) {
  const badge = trainer.importance_reason
    ? IMPORTANCE_BADGES[trainer.importance_reason]
    : null;

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  return (
    <div
      style={{
        padding: '12px 16px',
        borderRadius: '10px',
        border: highlight
          ? '2px solid var(--color-pokemon-primary)'
          : '1px solid var(--color-border)',
        backgroundColor: 'var(--color-bg-card)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {trainer.trainer_image && (
          <img
            src={trainer.trainer_image}
            alt={trainer.trainer_name}
            style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
          />
        )}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{trainer.trainer_name}</span>
            {badge && (
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  backgroundColor: badge.color,
                  color: 'white',
                  textTransform: 'uppercase',
                  letterSpacing: '0.3px',
                }}
              >
                {badge.label}
              </span>
            )}
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
            {trainer.location}
          </span>
        </div>
      </div>

      {/* Pokemon lineup */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '6px',
        }}
      >
        {trainer.pokemon.map((poke, idx) => (
          <PokemonEntry key={idx} poke={poke} apiBaseUrl={apiBaseUrl} />
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/frontend/src/components/TrainerCard.tsx
git commit -m "feat: add TrainerCard component with expandable stat bars"
```

---

### Task 9: Create TrainersPage

**Files:**
- Create: `src/frontend/src/pages/TrainersPage.tsx`
- Modify: `src/frontend/src/App.tsx`

**Step 1: Create the TrainersPage**

Create `src/frontend/src/pages/TrainersPage.tsx`:

```typescript
import { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useGameFile } from '../contexts/GameFileContext';
import { useTrainersByGame, useImportantTrainers } from '../hooks/useTrainers';
import { TrainerCard } from '../components/TrainerCard';
import type { Trainer } from '../types/trainer';

const SECTIONS_PER_PAGE = 15;

export function TrainersPage() {
  const { currentGameFile } = useGameFile();
  const [searchParams] = useSearchParams();
  const gameName = currentGameFile?.game_name ?? searchParams.get('gameName');
  // TODO: starter will come from currentGameFile.starter_selected once added
  const starter = undefined;

  const { data: allTrainers, isLoading } = useTrainersByGame(gameName, starter);
  const { data: importantTrainers } = useImportantTrainers(gameName, starter);

  const [expandedLocations, setExpandedLocations] = useState<Set<string>>(new Set());
  const [visibleSections, setVisibleSections] = useState(SECTIONS_PER_PAGE);

  // Group trainers by location in battle_order
  const locationGroups = useMemo(() => {
    if (!allTrainers) return [];
    const groups: { location: string; trainers: Trainer[] }[] = [];
    const seen = new Map<string, number>();

    for (const trainer of allTrainers) {
      const loc = trainer.location || 'Unknown';
      if (seen.has(loc)) {
        groups[seen.get(loc)!].trainers.push(trainer);
      } else {
        seen.set(loc, groups.length);
        groups.push({ location: loc, trainers: [trainer] });
      }
    }
    return groups;
  }, [allTrainers]);

  const toggleLocation = (location: string) => {
    setExpandedLocations((prev) => {
      const next = new Set(prev);
      if (next.has(location)) {
        next.delete(location);
      } else {
        next.add(location);
      }
      return next;
    });
  };

  if (!gameName) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        No game selected. Go to Dashboard first.
      </div>
    );
  }

  return (
    <div
      style={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      <h1 style={{ fontSize: '1.3rem', fontWeight: 700 }}>
        Trainers — {gameName}
      </h1>

      {isLoading && (
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading trainers...</p>
      )}

      {/* Key Battles section */}
      {importantTrainers && importantTrainers.length > 0 && (
        <div
          className="card"
          style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}
        >
          <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-pokemon-primary)' }}>
            Key Battles
          </div>
          {importantTrainers.map((trainer) => (
            <TrainerCard key={trainer.id} trainer={trainer} highlight />
          ))}
        </div>
      )}

      {/* Route-grouped accordion */}
      {locationGroups.slice(0, visibleSections).map((group) => {
        const isExpanded = expandedLocations.has(group.location);
        const importantCount = group.trainers.filter((t) => t.is_important).length;

        return (
          <div
            key={group.location}
            className="card"
            style={{ padding: '0', overflow: 'hidden' }}
          >
            <button
              type="button"
              onClick={() => toggleLocation(group.location)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: 'var(--color-text-primary)',
                fontSize: '0.9rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 700 }}>{group.location}</span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-text-secondary)',
                    backgroundColor: 'var(--color-bg-light)',
                    padding: '2px 8px',
                    borderRadius: '10px',
                  }}
                >
                  {group.trainers.length} trainer{group.trainers.length !== 1 ? 's' : ''}
                </span>
                {importantCount > 0 && (
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--color-pokemon-primary)',
                      color: 'white',
                    }}
                  >
                    {importantCount} key
                  </span>
                )}
              </div>
              <span style={{ fontSize: '0.8rem' }}>{isExpanded ? '▲' : '▼'}</span>
            </button>

            {isExpanded && (
              <div
                style={{
                  padding: '0 16px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                {group.trainers.map((trainer) => (
                  <TrainerCard key={trainer.id} trainer={trainer} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Load more */}
      {visibleSections < locationGroups.length && (
        <button
          type="button"
          onClick={() => setVisibleSections((prev) => prev + SECTIONS_PER_PAGE)}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-bg-light)',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 600,
          }}
        >
          Load more ({locationGroups.length - visibleSections} remaining)
        </button>
      )}
    </div>
  );
}
```

**Step 2: Add route to App.tsx**

Add import at top of `src/frontend/src/App.tsx`:

```typescript
import { TrainersPage } from './pages/TrainersPage';
```

Add route inside `<Routes>`, after the gyms route:

```tsx
<Route
  path="/trainers"
  element={
    <ProtectedRoute>
      <TrainersPage />
    </ProtectedRoute>
  }
/>
```

**Step 3: Commit**

```bash
git add src/frontend/src/pages/TrainersPage.tsx src/frontend/src/App.tsx
git commit -m "feat: add TrainersPage with key battles and accordion layout"
```

---

### Task 10: Add "View Trainers" button to Dashboard

**Files:**
- Modify: `src/frontend/src/pages/DashboardPage.tsx`

**Step 1: Add the button**

In `src/frontend/src/pages/DashboardPage.tsx`, find the "Add Pokemon" button block (the 4th action button, around line 419-460). Insert a new button **before** it (after the "View Team" button's closing `</button>` tag around line 417).

Add this button block following the exact same inline style pattern as the other action buttons:

```tsx
              {/* View Trainers button */}
              <button
                type="button"
                onClick={() => navigate(`/trainers?gameName=${encodeURIComponent(currentGameFile?.game_name ?? '')}`)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-light)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  fontSize: '0.9rem',
                  transition: 'all 150ms ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.color = 'white';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans.forEach((span) => {
                    (span as HTMLElement).style.color = 'rgba(255, 255, 255, 0.95)';
                  });
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.color = 'var(--color-text-primary)';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans[0].style.color = '';
                  (spans[1] as HTMLElement).style.color = 'var(--color-text-secondary)';
                }}
              >
                <span style={{ fontWeight: 600 }}>View Trainers</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  Browse all trainers & key battles
                </span>
              </button>
```

**Step 2: Commit**

```bash
git add src/frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add View Trainers button to dashboard next actions"
```

---

### Task 11: Add trainer avatars to RoutesPage

**Files:**
- Modify: `src/frontend/src/pages/RoutesPage.tsx`

**Step 1: Add trainer avatar row to route cards**

This task modifies the RoutesPage to show small trainer avatars below each route's encounter grid. The implementation needs to:

1. Import `useTrainersByRoute` from `../hooks/useTrainers`
2. Import `useNavigate` if not already imported
3. For each route card that has a `route.id`, fetch trainers for that route
4. Below the encounter grid, render a row of small circular trainer sprites
5. Clicking a trainer avatar navigates to `/trainers` with the trainer highlighted

Due to the large number of routes potentially visible, create a small inline component `RouteTrainerAvatars` that takes a `routeId` and renders the avatars. This component calls `useTrainersByRoute` internally — React Query handles caching so repeated renders don't re-fetch.

Add inside the route card, after the encounters grid section:

```tsx
function RouteTrainerAvatars({ routeId }: { routeId: number }) {
  const { data: trainers } = useTrainersByRoute(routeId);
  const navigate = useNavigate();

  if (!trainers || trainers.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px', alignItems: 'center' }}>
      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
        Trainers:
      </span>
      {trainers.map((trainer) => (
        <button
          key={trainer.id}
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/trainers?gameName=${encodeURIComponent(trainer.game_names[0] ?? '')}`);
          }}
          title={trainer.trainer_name}
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            border: trainer.is_important
              ? '2px solid var(--color-pokemon-primary)'
              : '1px solid var(--color-border)',
            backgroundColor: 'var(--color-bg-light)',
            padding: '2px',
            cursor: 'pointer',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {trainer.trainer_image ? (
            <img
              src={trainer.trainer_image}
              alt={trainer.trainer_name}
              style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
            />
          ) : (
            <span style={{ fontSize: '0.6rem' }}>?</span>
          )}
        </button>
      ))}
    </div>
  );
}
```

Place `<RouteTrainerAvatars routeId={route.id} />` after the encounter grid in each route card. The exact insertion point depends on where the encounter mapping ends in the route card JSX — look for the closing `</div>` of the encounters container and place it after.

Note: If `route.id` is not currently passed through to the frontend, you may need to update the route API response to include `id`. Check the routes router and schema — the Route model has an `id` field, so it should be available.

**Step 2: Commit**

```bash
git add src/frontend/src/pages/RoutesPage.tsx
git commit -m "feat: add trainer avatars to route cards"
```

---

### Task 12: End-to-end verification

**Step 1: Start the backend**

```bash
cd src/backend
taskkill /F /IM python.exe 2>nul
python -c "import uvicorn; uvicorn.run('api.main:app', host='0.0.0.0', port=8000)"
```

**Step 2: Start the frontend (separate terminal)**

```bash
cd src/frontend
pnpm dev
```

**Step 3: Verify in browser**

1. Log in and select a game file
2. On Dashboard, verify "View Trainers" button appears in Next Actions
3. Click "View Trainers" — verify TrainersPage loads with Key Battles and accordion
4. Expand an accordion section — verify TrainerCards render with pokemon sprites
5. Click a pokemon in a TrainerCard — verify stats expand with bar charts
6. Go to Routes page — verify trainer avatars appear on routes that have trainers
7. Click a trainer avatar — verify navigation to TrainersPage

**Step 4: Final commit**

If any fixes were needed during verification, commit them:

```bash
git add -A
git commit -m "fix: polish trainer feature after e2e verification"
```
