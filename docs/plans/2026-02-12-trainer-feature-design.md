# Trainer Feature Design

**Date:** 2026-02-12
**Status:** Approved

## Overview

Add a comprehensive trainer browsing system: a `Trainer` database table populated from the Gen JSON data files (`src/data/Gen*/*.json`), with precomputed true stats for each trainer's Pokemon. Trainers are fuzzy-matched to existing routes, flagged for importance, and displayed in a new Trainers page accessible from the Dashboard. Route pages also show linked trainers.

## Data Source

Primary: `src/data/Gen*/*.json` files. These contain all trainers (rivals, gym leaders, grunts, elite four, champions) with DVs, moves, and sprite paths. The `src/backend/scrape/trainer_data/` files are NOT used — they only cover gym leaders with less data.

## Data Model

### New `Trainer` Table

```
Trainer
├── id: Integer (PK, auto-increment)
├── generation: Integer                  # 1, 2, 3, etc.
├── game_names: ARRAY(String)            # ["red", "blue"] or ["diamond", "pearl"]
├── trainer_name: String                 # "Brock", "Rival 1", "Grunt"
├── trainer_image: String                # Sprite path/URL
├── location: String                     # Raw location from JSON
├── route_id: Integer (FK → Route.id, nullable)  # Fuzzy-matched route
├── is_important: Boolean                # Computed by importance algorithm
├── importance_reason: String (nullable) # "gym_leader", "rival", "champion", etc.
├── starter_filter: String (nullable)    # "Bulbasaur" or null (null = all starters)
├── battle_order: Integer                # Index in JSON array (game progression)
├── pokemon: JSON                        # Precomputed array (see below)
└── created_at: Timestamp
```

### Pokemon JSON Schema (precomputed)

```json
[
  {
    "name": "Geodude",
    "poke_id": 74,
    "level": 12,
    "moves": ["Tackle", "Defense Curl"],
    "stats": {
      "hp": 30,
      "attack": 25,
      "defense": 35,
      "special_attack": 15,
      "special_defense": 15,
      "speed": 10
    }
  }
]
```

Stats are computed at population time using `calc.py`'s `_calculate_stat()` with base stats from `AllPokemon` + DVs from the JSON + level. EVs assumed 0.

### Assumption

`GameFiles.starter_selected: str` will be added by the user separately. The trainer feature filters starter variants using this field.

## Important Trainer Algorithm

Two signals combined at population time:

### 1. Role-Based Detection

Pattern match on `trainer_name`:
- **Rival**: contains "Rival"
- **Gym Leader**: cross-reference existing `Gym` table's `trainer_name` values
- **Elite Four / Champion**: known names or location contains "Elite Four", "Champion"
- **Evil Team Leaders/Admins**: keywords "Boss", "Admin", "Leader" + team names ("Rocket", "Magma", "Aqua", "Galactic", "Plasma", "Flare", "Skull", "Yell", "Star")

### 2. Level Outlier Detection

For trainers not caught by role-based detection:
- Compute the median avg Pokemon level of all trainers within a ±3 `battle_order` window
- If a trainer's avg level exceeds the window median by >20%, flag as important

### Result

`is_important = True` with `importance_reason` set to first match: `"gym_leader"`, `"rival"`, `"evil_team_leader"`, `"elite_four"`, `"champion"`, or `"level_outlier"`.

## Route-to-Trainer Fuzzy Matching

Runs at population time for each trainer's `location` string against `Route.name` values for the same version.

### Algorithm

1. Normalize both strings: lowercase, strip whitespace, remove punctuation (`'`, `-`, `.`)
2. Token overlap score: split into word tokens, compute Jaccard similarity (`|intersection| / |union|`)
3. Accept match if score >= 0.8
4. If no match at 0.8, try substring containment (e.g., `"Lab"` contained in `"Professor Oak's Lab"`)
5. If still no match, `route_id` stays `NULL`

No manual override maps — pure algorithmic matching.

## API Endpoints

### New Router: `routers/trainers.py`

```
GET /api/trainers/{game_name}
  → All trainers for a game, ordered by battle_order
  → Query params: ?starter={starter_name}
  → Returns: trainer list with pokemon (including stats)

GET /api/trainers/{game_name}/important
  → Only important trainers for a game
  → Query params: ?starter={starter_name}

GET /api/trainers/by-route/{route_id}
  → All trainers matched to a specific route
  → Query params: ?starter={starter_name}
```

Sprite resolution handled by frontend — API returns `poke_id`, frontend resolves sprites via `AllPokemon` the same way it does everywhere else.

## Frontend UI

### Trainers Page (`/trainers`)

Accessed via a new "View Trainers" button in the Dashboard's next actions section.

**Layout:**
- **Top: "Key Battles" pinned section** — all `is_important` trainers as highlighted cards in game order. Always visible, not collapsible.
- **Below: Route-grouped accordion** — every route/location as a collapsible section in `battle_order` order. Section header shows location name + trainer count. Collapsed by default.
- Important trainers within accordion sections get a visual badge/star.
- Lazy loading: ~15 sections at a time, consistent with RoutesPage pagination pattern.

### Trainer Card Component

- Trainer sprite image
- Trainer name + importance badge if applicable
- Location name
- Pokemon lineup (horizontal):
  - Pokemon sprite (from `AllPokemon` via `poke_id`)
  - Name, level
  - Expandable stats panel (click to reveal HP/Atk/Def/SpA/SpD/Spe bar chart)
  - Moves list

### Route Page Integration

On the Routes page, for each route card:
- If trainers exist for that route (via `route_id`), show a trainer avatar row — small circular trainer sprites below the encounter grid
- Clicking a trainer avatar navigates to `/trainers` and scrolls/highlights that trainer's card
- If no trainers matched, nothing shown

## Architecture: Precompute at Population Time

- A `populate_trainers.py` script reads Gen JSON files, computes true stats via `calc.py` + `AllPokemon` base stats, runs fuzzy route matching, runs the importance algorithm, and inserts into the `Trainer` table.
- No runtime computation — API is a simple read from the DB.
- Trainer data is static game data that never changes after population.

## Game-to-JSON Mapping

| JSON File | game_names | generation |
|-----------|-----------|------------|
| Gen1/RedBlue.json | ["red", "blue"] | 1 |
| Gen1/Yellow.json | ["yellow"] | 1 |
| Gen2/GS.json | ["gold", "silver"] | 2 |
| Gen2/Crystal.json | ["crystal"] | 2 |
| Gen3/RS.json | ["ruby", "sapphire"] | 3 |
| Gen3/FRLG.json | ["firered", "leafgreen"] | 3 |
| Gen3/Emerald.json | ["emerald"] | 3 |
| Gen4/DP.json | ["diamond", "pearl"] | 4 |
| Gen4/Plat.json | ["platinum"] | 4 |
| Gen4/HGSS.json | ["heartgold", "soulsilver"] | 4 |
| Gen5/BW.json | ["black", "white"] | 5 |
| Gen5/B2W2.json | ["black 2", "white 2"] | 5 |
| Gen6/XY.json | ["x", "y"] | 6 |
| Gen6/ORAS.json | ["omega ruby", "alpha sapphire"] | 6 |
| Gen7/SM.json | ["sun", "moon"] | 7 |
| Gen7/USUM.json | ["ultra sun", "ultra moon"] | 7 |
| Gen8/SS.json | ["sword", "shield"] | 8 |
| Gen8/BDSP.json | ["brilliant diamond", "shining pearl"] | 8 |
| Gen9/SV.json | ["scarlet", "violet"] | 9 |
