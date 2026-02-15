"""
Rework scrape/trainer_data JSON files:
1. Download gym badge images from Bulbapedia -> src/data/badges/*.webp
2. Replace trainer_image URLs with local sprite paths
3. Add badge_image attribute pointing to local badge webp

Usage:
    python rework_scrape_data.py
"""

import json
import os
import re
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent              # src/backend/scrape
BACKEND_DIR = SCRIPT_DIR.parent                           # src/backend
DATA_DIR = BACKEND_DIR.parent / "data"                    # src/data
SPRITES_DIR = DATA_DIR / "sprites"                        # src/data/sprites
BADGES_DIR = DATA_DIR / "badges"                          # src/data/badges
TRAINER_DATA_DIR = SCRIPT_DIR / "trainer_data"            # src/backend/scrape/trainer_data

# ---------------------------------------------------------------------------
# Scrape file -> sprite prefix mapping
# ---------------------------------------------------------------------------
SCRAPE_SPRITE_PREFIX = {
    "red-blue_trainers.json": "rg",
    "yellow_trainers.json": "y",
    "gold-silver_trainers.json": "gs",
    "crystal_trainers.json": "gs",
    "ruby-sapphire_trainers.json": "rs",
    "firered-leafgreen_trainers.json": "frlg",
    "diamond-pearl_trainers.json": "dp",
    "platinum_trainers.json": "dp",
    "heartgold-soulsilver_trainers.json": "hgss",
    "black-white_trainers.json": "bw",
    "black-white-2_trainers.json": "b2w2",
}

# ---------------------------------------------------------------------------
# Badge image URLs (full-resolution from Bulbapedia archives)
# Format: https://archives.bulbagarden.net/media/upload/{path}/{Name}_Badge.png
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Badge images are stored as {game_name}_{gym#}.webp where game_name matches
# the Gym table's game_name column (PokeAPI version names).
# ---------------------------------------------------------------------------

# Unique badge images to download (badge_name -> Bulbapedia URL).
BADGE_URLS = {
    "Boulder Badge": "https://archives.bulbagarden.net/media/upload/d/dd/Boulder_Badge.png",
    "Cascade Badge": "https://archives.bulbagarden.net/media/upload/9/9c/Cascade_Badge.png",
    "Thunder Badge": "https://archives.bulbagarden.net/media/upload/a/a6/Thunder_Badge.png",
    "Rainbow Badge": "https://archives.bulbagarden.net/media/upload/b/b5/Rainbow_Badge.png",
    "Soul Badge": "https://archives.bulbagarden.net/media/upload/7/7d/Soul_Badge.png",
    "Marsh Badge": "https://archives.bulbagarden.net/media/upload/6/6b/Marsh_Badge.png",
    "Volcano Badge": "https://archives.bulbagarden.net/media/upload/1/12/Volcano_Badge.png",
    "Earth Badge": "https://archives.bulbagarden.net/media/upload/7/78/Earth_Badge.png",
    "Zephyr Badge": "https://archives.bulbagarden.net/media/upload/4/4a/Zephyr_Badge.png",
    "Hive Badge": "https://archives.bulbagarden.net/media/upload/0/08/Hive_Badge.png",
    "Plain Badge": "https://archives.bulbagarden.net/media/upload/a/a7/Plain_Badge.png",
    "Fog Badge": "https://archives.bulbagarden.net/media/upload/4/48/Fog_Badge.png",
    "Storm Badge": "https://archives.bulbagarden.net/media/upload/b/b9/Storm_Badge.png",
    "Mineral Badge": "https://archives.bulbagarden.net/media/upload/7/7b/Mineral_Badge.png",
    "Glacier Badge": "https://archives.bulbagarden.net/media/upload/e/e6/Glacier_Badge.png",
    "Rising Badge": "https://archives.bulbagarden.net/media/upload/5/58/Rising_Badge.png",
    "Stone Badge": "https://archives.bulbagarden.net/media/upload/6/63/Stone_Badge.png",
    "Knuckle Badge": "https://archives.bulbagarden.net/media/upload/9/97/Knuckle_Badge.png",
    "Dynamo Badge": "https://archives.bulbagarden.net/media/upload/3/34/Dynamo_Badge.png",
    "Heat Badge": "https://archives.bulbagarden.net/media/upload/c/c4/Heat_Badge.png",
    "Balance Badge": "https://archives.bulbagarden.net/media/upload/6/63/Balance_Badge.png",
    "Feather Badge": "https://archives.bulbagarden.net/media/upload/6/62/Feather_Badge.png",
    "Mind Badge": "https://archives.bulbagarden.net/media/upload/c/cc/Mind_Badge.png",
    "Rain Badge": "https://archives.bulbagarden.net/media/upload/9/9b/Rain_Badge.png",
    "Coal Badge": "https://archives.bulbagarden.net/media/upload/0/0b/Coal_Badge.png",
    "Forest Badge": "https://archives.bulbagarden.net/media/upload/8/8c/Forest_Badge.png",
    "Cobble Badge": "https://archives.bulbagarden.net/media/upload/2/27/Cobble_Badge.png",
    "Fen Badge": "https://archives.bulbagarden.net/media/upload/1/13/Fen_Badge.png",
    "Relic Badge": "https://archives.bulbagarden.net/media/upload/2/28/Relic_Badge.png",
    "Mine Badge": "https://archives.bulbagarden.net/media/upload/f/fe/Mine_Badge.png",
    "Icicle Badge": "https://archives.bulbagarden.net/media/upload/0/09/Icicle_Badge.png",
    "Beacon Badge": "https://archives.bulbagarden.net/media/upload/0/0c/Beacon_Badge.png",
    "Trio Badge": "https://archives.bulbagarden.net/media/upload/7/74/Trio_Badge.png",
    "Basic Badge": "https://archives.bulbagarden.net/media/upload/8/85/Basic_Badge.png",
    "Insect Badge": "https://archives.bulbagarden.net/media/upload/8/8a/Insect_Badge.png",
    "Bolt Badge": "https://archives.bulbagarden.net/media/upload/5/5b/Bolt_Badge.png",
    "Quake Badge": "https://archives.bulbagarden.net/media/upload/2/29/Quake_Badge.png",
    "Jet Badge": "https://archives.bulbagarden.net/media/upload/9/9c/Jet_Badge.png",
    "Freeze Badge": "https://archives.bulbagarden.net/media/upload/a/ac/Freeze_Badge.png",
    "Legend Badge": "https://archives.bulbagarden.net/media/upload/c/c0/Legend_Badge.png",
    "Toxic Badge": "https://archives.bulbagarden.net/media/upload/3/3e/Toxic_Badge.png",
    "Wave Badge": "https://archives.bulbagarden.net/media/upload/0/00/Wave_Badge.png",
}

# Ordered badge names for each region (gym 1 through 8).
_KANTO_BADGES = [
    "Boulder Badge", "Cascade Badge", "Thunder Badge", "Rainbow Badge",
    "Soul Badge", "Marsh Badge", "Volcano Badge", "Earth Badge",
]
_JOHTO_BADGES = [
    "Zephyr Badge", "Hive Badge", "Plain Badge", "Fog Badge",
    "Storm Badge", "Mineral Badge", "Glacier Badge", "Rising Badge",
]
_HOENN_BADGES = [
    "Stone Badge", "Knuckle Badge", "Dynamo Badge", "Heat Badge",
    "Balance Badge", "Feather Badge", "Mind Badge", "Rain Badge",
]
_SINNOH_BADGES = [
    "Coal Badge", "Forest Badge", "Cobble Badge", "Fen Badge",
    "Relic Badge", "Mine Badge", "Icicle Badge", "Beacon Badge",
]
_BW_BADGES = [
    "Trio Badge", "Basic Badge", "Insect Badge", "Bolt Badge",
    "Quake Badge", "Jet Badge", "Freeze Badge", "Legend Badge",
]
_B2W2_BADGES = [
    "Basic Badge", "Toxic Badge", "Insect Badge", "Bolt Badge",
    "Quake Badge", "Jet Badge", "Legend Badge", "Wave Badge",
]

# Maps game_name (PokeAPI version name) -> list of badge names in gym order.
# HGSS gets gyms 1-8 (Johto) + 9-16 (Kanto).
GAME_BADGE_ORDER: dict[str, list[str]] = {
    "red": _KANTO_BADGES, "blue": _KANTO_BADGES,
    "yellow": _KANTO_BADGES,
    "gold": _JOHTO_BADGES, "silver": _JOHTO_BADGES,
    "crystal": _JOHTO_BADGES,
    "ruby": _HOENN_BADGES, "sapphire": _HOENN_BADGES,
    "emerald": _HOENN_BADGES,
    "firered": _KANTO_BADGES, "leafgreen": _KANTO_BADGES,
    "diamond": _SINNOH_BADGES, "pearl": _SINNOH_BADGES,
    "platinum": _SINNOH_BADGES,
    "heartgold": _JOHTO_BADGES + _KANTO_BADGES,
    "soulsilver": _JOHTO_BADGES + _KANTO_BADGES,
    "black": _BW_BADGES, "white": _BW_BADGES,
    "black-2": _B2W2_BADGES, "white-2": _B2W2_BADGES,
}

# Maps scrape filename -> list of game_names that share this data file.
# The first game_name is used as the "primary" for badge_image in the JSON.
SCRAPE_GAME_NAMES: dict[str, list[str]] = {
    "red-blue_trainers.json": ["red", "blue"],
    "yellow_trainers.json": ["yellow"],
    "gold-silver_trainers.json": ["gold", "silver"],
    "crystal_trainers.json": ["crystal"],
    "ruby-sapphire_trainers.json": ["ruby", "sapphire"],
    "firered-leafgreen_trainers.json": ["firered", "leafgreen"],
    "diamond-pearl_trainers.json": ["diamond", "pearl"],
    "platinum_trainers.json": ["platinum"],
    "heartgold-soulsilver_trainers.json": ["heartgold", "soulsilver"],
    "black-white_trainers.json": ["black", "white"],
    "black-white-2_trainers.json": ["black-2", "white-2"],
}

HEADERS = {
    "User-Agent": "NuzlockeTracker/1.0 (educational project; badge image download)"
}


# ---------------------------------------------------------------------------
# Badge downloading
# ---------------------------------------------------------------------------

def download_badges() -> dict[str, str]:
    """
    Download unique badge images from Bulbapedia, then create per-game copies
    as {game_name}_{gym#}.webp.  Returns file_stem -> relative path map for
    all created files.
    """
    import shutil

    BADGES_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Download unique badge images (keyed by badge name).
    badge_data: dict[str, bytes] = {}
    for badge_name, url in BADGE_URLS.items():
        # Use first existing game file as cache check.
        # If any game copy exists, read it instead of re-downloading.
        cached = False
        for game_name, badges in GAME_BADGE_ORDER.items():
            if badge_name in badges:
                gym_num = badges.index(badge_name) + 1
                cache_path = BADGES_DIR / f"{game_name}_{gym_num}.webp"
                if cache_path.exists():
                    badge_data[badge_name] = cache_path.read_bytes()
                    cached = True
                    break

        if cached:
            print(f"  [CACHED] {badge_name}")
            continue

        try:
            print(f"  Downloading {badge_name}...")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            buf = BytesIO()
            img.save(buf, "WEBP", quality=90)
            badge_data[badge_name] = buf.getvalue()
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] {badge_name}: {e}")

    # Step 2: Create {game_name}_{gym#}.webp files for every game.
    badge_paths: dict[str, str] = {}
    created = 0
    for game_name, badges in GAME_BADGE_ORDER.items():
        for gym_num_0, badge_name in enumerate(badges):
            gym_num = gym_num_0 + 1
            file_stem = f"{game_name}_{gym_num}"
            filename = f"{file_stem}.webp"
            out_path = BADGES_DIR / filename
            rel_path = f"../data/badges/{filename}"

            if badge_name not in badge_data:
                print(f"  [SKIP] {file_stem} — no image for {badge_name}")
                continue

            if not out_path.exists():
                out_path.write_bytes(badge_data[badge_name])
                created += 1

            badge_paths[file_stem] = rel_path

    print(f"  Created {created} new badge files ({len(badge_paths)} total).")
    return badge_paths


# ---------------------------------------------------------------------------
# Trainer sprite matching (reuses logic from populate_trainers.py)
# ---------------------------------------------------------------------------

def _build_sprite_lookup(prefix: str) -> dict[str, str]:
    """Build sprite class name -> full stem lookup for a prefix."""
    if not SPRITES_DIR.exists():
        return {}
    lookup: dict[str, str] = {}
    prefix_len = len(prefix) + 1
    for f in SPRITES_DIR.iterdir():
        if not f.name.startswith(prefix + "_") or f.suffix != ".webp":
            continue
        stem = f.stem
        class_part = stem[prefix_len:]
        parts = class_part.split("_")
        for i in range(len(parts)):
            sub_key = "_".join(parts[i:])
            if sub_key not in lookup or len(class_part) > len(lookup[sub_key]):
                lookup[sub_key] = stem
    return lookup


def _resolve_sprite(trainer_name: str, prefix: str, sprite_lookup: dict[str, str]) -> str:
    """
    Map a trainer name to a local sprite path.
    Tries: exact normalized match, containment, then Jaccard.
    """
    if not sprite_lookup or not prefix:
        return ""

    name = trainer_name.strip().lower().replace(".", "").replace("'", "")
    # The scrape data only has important trainers (gym leaders, E4, champion)
    # so names are usually just the character name like "Brock", "Lorelei"
    normalized = name.replace(" ", "_")

    # Direct match
    if normalized in sprite_lookup:
        return f"../data/sprites/{sprite_lookup[normalized]}.webp"

    # Try just the last word (handles "Lt. Surge" -> "surge" matching "lt_surge")
    tokens = name.split()
    if tokens:
        last = tokens[-1]
        if last in sprite_lookup:
            return f"../data/sprites/{sprite_lookup[last]}.webp"

    # Containment
    best = ""
    best_len = 0
    for key, stem in sprite_lookup.items():
        if key in normalized or normalized in key:
            if len(key) > best_len:
                best = stem
                best_len = len(key)
    if best and best_len >= 3:
        return f"../data/sprites/{best}.webp"

    return ""


# ---------------------------------------------------------------------------
# Rewrite scrape JSON files
# ---------------------------------------------------------------------------

def rewrite_scrape_files(badge_paths: dict[str, str]) -> None:
    """
    Iterate each scrape JSON, update trainer_image to local paths,
    add badge_image attribute using {game_name}_{gym#} naming.
    """
    for filename in sorted(TRAINER_DATA_DIR.glob("*.json")):
        prefix = SCRAPE_SPRITE_PREFIX.get(filename.name, "")
        sprite_lookup = _build_sprite_lookup(prefix) if prefix else {}

        # Use the first game_name for this scrape file as the badge prefix.
        game_names = SCRAPE_GAME_NAMES.get(filename.name, [])
        primary_game = game_names[0] if game_names else ""

        print(f"\n--- {filename.name} (prefix={prefix}, game={primary_game}, sprites={len(sprite_lookup)}) ---")

        with open(filename, "r", encoding="utf-8") as f:
            entries = json.load(f)

        updated = 0
        for entry in entries:
            # Update trainer_image
            trainer_name = entry.get("trainer_name", "")
            new_image = _resolve_sprite(trainer_name, prefix, sprite_lookup)

            if new_image:
                entry["trainer_image"] = new_image
                updated += 1
            # If no local match, keep the old URL as fallback

            # Add badge_image using {game_name}_{gym#} naming.
            gym_number = entry.get("gym_number", "")
            if primary_game and gym_number:
                file_stem = f"{primary_game}_{gym_number}"
                entry["badge_image"] = badge_paths.get(file_stem, "")
            else:
                entry["badge_image"] = ""

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

        print(f"  Updated {updated}/{len(entries)} trainer images, added badge_image to all entries.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Step 1: Download badge images ===\n")
    badge_paths = download_badges()
    print(f"\nDownloaded {sum(1 for v in badge_paths.values() if v)} badges.\n")

    print("=== Step 2: Rewrite scrape JSON files ===")
    rewrite_scrape_files(badge_paths)

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
