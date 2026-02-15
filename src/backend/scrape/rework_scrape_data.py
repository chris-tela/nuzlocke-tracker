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
BADGE_URLS = {
    # Kanto
    "Boulder Badge": "https://archives.bulbagarden.net/media/upload/d/dd/Boulder_Badge.png",
    "Cascade Badge": "https://archives.bulbagarden.net/media/upload/9/9c/Cascade_Badge.png",
    "Thunder Badge": "https://archives.bulbagarden.net/media/upload/a/a6/Thunder_Badge.png",
    "Rainbow Badge": "https://archives.bulbagarden.net/media/upload/b/b5/Rainbow_Badge.png",
    "Soul Badge": "https://archives.bulbagarden.net/media/upload/7/7d/Soul_Badge.png",
    "Marsh Badge": "https://archives.bulbagarden.net/media/upload/6/6b/Marsh_Badge.png",
    "Volcano Badge": "https://archives.bulbagarden.net/media/upload/1/12/Volcano_Badge.png",
    "Earth Badge": "https://archives.bulbagarden.net/media/upload/7/78/Earth_Badge.png",
    # Johto
    "Zephyr Badge": "https://archives.bulbagarden.net/media/upload/4/4a/Zephyr_Badge.png",
    "Hive Badge": "https://archives.bulbagarden.net/media/upload/0/08/Hive_Badge.png",
    "Plain Badge": "https://archives.bulbagarden.net/media/upload/a/a7/Plain_Badge.png",
    "Fog Badge": "https://archives.bulbagarden.net/media/upload/4/48/Fog_Badge.png",
    "Storm Badge": "https://archives.bulbagarden.net/media/upload/b/b9/Storm_Badge.png",
    "Mineral Badge": "https://archives.bulbagarden.net/media/upload/7/7b/Mineral_Badge.png",
    "Glacier Badge": "https://archives.bulbagarden.net/media/upload/e/e6/Glacier_Badge.png",
    "Rising Badge": "https://archives.bulbagarden.net/media/upload/5/58/Rising_Badge.png",
    # Hoenn
    "Stone Badge": "https://archives.bulbagarden.net/media/upload/6/63/Stone_Badge.png",
    "Knuckle Badge": "https://archives.bulbagarden.net/media/upload/9/97/Knuckle_Badge.png",
    "Dynamo Badge": "https://archives.bulbagarden.net/media/upload/3/34/Dynamo_Badge.png",
    "Heat Badge": "https://archives.bulbagarden.net/media/upload/c/c4/Heat_Badge.png",
    "Balance Badge": "https://archives.bulbagarden.net/media/upload/6/63/Balance_Badge.png",
    "Feather Badge": "https://archives.bulbagarden.net/media/upload/6/62/Feather_Badge.png",
    "Mind Badge": "https://archives.bulbagarden.net/media/upload/c/cc/Mind_Badge.png",
    "Rain Badge": "https://archives.bulbagarden.net/media/upload/9/9b/Rain_Badge.png",
    # Sinnoh
    "Coal Badge": "https://archives.bulbagarden.net/media/upload/0/0b/Coal_Badge.png",
    "Forest Badge": "https://archives.bulbagarden.net/media/upload/8/8c/Forest_Badge.png",
    "Cobble Badge": "https://archives.bulbagarden.net/media/upload/2/27/Cobble_Badge.png",
    "Fen Badge": "https://archives.bulbagarden.net/media/upload/1/13/Fen_Badge.png",
    "Relic Badge": "https://archives.bulbagarden.net/media/upload/2/28/Relic_Badge.png",
    "Mine Badge": "https://archives.bulbagarden.net/media/upload/f/fe/Mine_Badge.png",
    "Icicle Badge": "https://archives.bulbagarden.net/media/upload/0/09/Icicle_Badge.png",
    "Beacon Badge": "https://archives.bulbagarden.net/media/upload/0/0c/Beacon_Badge.png",
    # Unova (BW)
    "Trio Badge": "https://archives.bulbagarden.net/media/upload/7/74/Trio_Badge.png",
    "Basic Badge": "https://archives.bulbagarden.net/media/upload/8/85/Basic_Badge.png",
    "Insect Badge": "https://archives.bulbagarden.net/media/upload/8/8a/Insect_Badge.png",
    "Bolt Badge": "https://archives.bulbagarden.net/media/upload/5/5b/Bolt_Badge.png",
    "Quake Badge": "https://archives.bulbagarden.net/media/upload/2/29/Quake_Badge.png",
    "Jet Badge": "https://archives.bulbagarden.net/media/upload/9/9c/Jet_Badge.png",
    "Freeze Badge": "https://archives.bulbagarden.net/media/upload/a/ac/Freeze_Badge.png",
    "Legend Badge": "https://archives.bulbagarden.net/media/upload/c/c0/Legend_Badge.png",
    # Unova (B2W2)
    "Toxic Badge": "https://archives.bulbagarden.net/media/upload/3/3e/Toxic_Badge.png",
    "Wave Badge": "https://archives.bulbagarden.net/media/upload/0/00/Wave_Badge.png",
    # Extra (if referenced in scrape data)
    "Beetle Badge": "https://archives.bulbagarden.net/media/upload/8/8a/Insect_Badge.png",
}

HEADERS = {
    "User-Agent": "NuzlockeTracker/1.0 (educational project; badge image download)"
}


# ---------------------------------------------------------------------------
# Badge downloading
# ---------------------------------------------------------------------------

def download_badges() -> dict[str, str]:
    """
    Download all badge images from Bulbapedia, convert to webp,
    save to BADGES_DIR. Returns badge_name -> relative path map.
    """
    BADGES_DIR.mkdir(parents=True, exist_ok=True)
    badge_paths: dict[str, str] = {}

    for badge_name, url in BADGE_URLS.items():
        filename = badge_name.lower().replace(" ", "_") + ".webp"
        out_path = BADGES_DIR / filename
        rel_path = f"../data/badges/{filename}"

        if out_path.exists():
            print(f"  [SKIP] {badge_name} — already exists")
            badge_paths[badge_name] = rel_path
            continue

        try:
            print(f"  Downloading {badge_name}...")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content))
            img.save(str(out_path), "WEBP", quality=90)
            badge_paths[badge_name] = rel_path
            print(f"    -> {filename} ({out_path.stat().st_size} bytes)")

            time.sleep(0.5)  # Be polite to Bulbapedia

        except Exception as e:
            print(f"  [ERROR] {badge_name}: {e}")
            badge_paths[badge_name] = ""

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
    add badge_image attribute.
    """
    for filename in sorted(TRAINER_DATA_DIR.glob("*.json")):
        prefix = SCRAPE_SPRITE_PREFIX.get(filename.name, "")
        sprite_lookup = _build_sprite_lookup(prefix) if prefix else {}

        print(f"\n--- {filename.name} (prefix={prefix}, sprites={len(sprite_lookup)}) ---")

        with open(filename, "r", encoding="utf-8") as f:
            entries = json.load(f)

        updated = 0
        for entry in entries:
            # Update trainer_image
            old_image = entry.get("trainer_image", "")
            trainer_name = entry.get("trainer_name", "")
            new_image = _resolve_sprite(trainer_name, prefix, sprite_lookup)

            if new_image:
                entry["trainer_image"] = new_image
                updated += 1
            # If no local match, keep the old URL as fallback

            # Add badge_image
            badge_name = entry.get("badge_name", "")
            entry["badge_image"] = badge_paths.get(badge_name, "")

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
