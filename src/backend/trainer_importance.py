import re
import statistics
from difflib import SequenceMatcher


RIVAL_KEYWORDS = ["rival"]

CHAMPION_KEYWORDS = ["champion"]

ELITE_FOUR_KEYWORDS = ["elite four"]

EVIL_TEAM_NAMES = [
    "rocket", "magma", "aqua", "galactic", "plasma",
    "flare", "skull", "yell", "star",
]

EVIL_ROLE_KEYWORDS = ["boss", "admin", "leader", "exec", "commander", "shadow"]

# Prefixes stripped when extracting the base trainer name.
_TRAINER_PREFIXES = [
    "pkmn trainer", "pokemon trainer", "pokémon trainer",
    "leader", "elite four", "admin", "commander",
]

# ---------------------------------------------------------------------------
# NOTABLE_TRAINERS: per-game hardcoded lookup for bosses, named rivals, and
# other important trainers that can't be reliably detected by pattern matching.
# Keys are tuples of game names (matching FILE_MAP values).
# Values map lowercased base name -> importance reason.
# ---------------------------------------------------------------------------
NOTABLE_TRAINERS: dict[tuple[str, ...], dict[str, str]] = {
    # Gen 1
    ("red", "blue"): {
        "giovanni": "evil_team_boss",
    },
    ("yellow",): {
        "giovanni": "evil_team_boss",
    },
    # Gen 2
    ("gold", "silver"): {
        "rocket exec": "evil_team_admin",
    },
    ("crystal",): {
        "rocket exec": "evil_team_admin",
        "eusine": "rival",
    },
    # Gen 3
    ("ruby", "sapphire"): {
        "archie": "evil_team_boss", "maxie": "evil_team_boss",
        "wally": "rival",
        "matt": "evil_team_admin", "shelly": "evil_team_admin",
        "courtney": "evil_team_admin", "tabitha": "evil_team_admin",
    },
    ("firered", "leafgreen"): {
        "giovanni": "evil_team_boss",
    },
    ("emerald",): {
        "archie": "evil_team_boss", "maxie": "evil_team_boss",
        "wally": "rival",
        "matt": "evil_team_admin", "shelly": "evil_team_admin",
        "courtney": "evil_team_admin", "tabitha": "evil_team_admin",
    },
    # Gen 4
    ("diamond", "pearl"): {
        "cyrus": "evil_team_boss",
        "mars": "evil_team_admin", "jupiter": "evil_team_admin",
        "saturn": "evil_team_admin",
        "barry": "rival",
    },
    ("platinum",): {
        "cyrus": "evil_team_boss",
        "mars": "evil_team_admin", "jupiter": "evil_team_admin",
        "saturn": "evil_team_admin",
        "barry": "rival",
    },
    ("heartgold", "soulsilver"): {
        "archer": "evil_team_admin", "ariana": "evil_team_admin",
        "proton": "evil_team_admin", "petrel": "evil_team_admin",
        "eusine": "rival",
        "red": "champion",
    },
    # Gen 5
    ("black", "white"): {
        "n": "evil_team_boss", "ghetsis": "evil_team_boss",
        "cheren": "rival", "bianca": "rival",
        "alder": "champion",
        "caitlin": "elite_four", "marshal": "elite_four",
    },
    ("black 2", "white 2"): {
        "ghetsis": "evil_team_boss",
        "colress": "evil_team_admin", "zinzolin": "evil_team_admin",
        "rood": "evil_team_admin",
    },
    # Gen 6
    ("x", "y"): {
        "lysandre": "evil_team_boss",
    },
    ("omega ruby", "alpha sapphire"): {
        "archie": "evil_team_boss", "maxie": "evil_team_boss",
        "wally": "rival",
        "matt": "evil_team_admin", "shelly": "evil_team_admin",
        "courtney": "evil_team_admin", "tabitha": "evil_team_admin",
    },
    # Gen 7
    ("sun", "moon"): {
        "guzma": "evil_team_boss", "gladion": "rival",
        "plumeria": "evil_team_admin",
    },
    ("ultra sun", "ultra moon"): {
        "guzma": "evil_team_boss", "gladion": "rival",
        "lusamine": "evil_team_boss",
        "lysandre": "evil_team_boss", "maxie": "evil_team_boss",
        "cyrus": "evil_team_boss", "ghetsis": "evil_team_boss",
    },
    # Gen 8
    ("sword", "shield"): {
        "leon": "champion",
    },
    ("brilliant diamond", "shining pearl"): {
        "cyrus": "evil_team_boss",
        "mars": "evil_team_admin", "jupiter": "evil_team_admin",
        "saturn": "evil_team_admin",
        "dawn": "rival", "palmer": "evil_team_boss",
    },
    # Gen 9
    ("scarlet", "violet"): {
        "arven": "rival", "geeta": "champion",
    },
}


def _extract_base_name(trainer_name: str) -> str:
    """
    Extract the base name from a trainer name by stripping known prefixes
    and trailing numbers.

    Examples:
        "Cyrus 1"              -> "cyrus"
        "N 5"                  -> "n"
        "Leader Giovanni"      -> "giovanni"
        "PKMN Trainer Wally"   -> "wally"
        "Admin Plumeria 1"     -> "plumeria"
        "Commander Jupiter 1"  -> "jupiter"
    """
    name = trainer_name.strip().lower()
    # Strip trailing number.
    name = re.sub(r"\s+\d+$", "", name)
    # Strip known prefixes.
    for prefix in _TRAINER_PREFIXES:
        if name.startswith(prefix + " "):
            name = name[len(prefix) + 1:]
            break
    return name.strip()


def _fuzzy_match_gym_leader(trainer_name: str, gym_leader_names: set[str]) -> bool:
    """
    Check whether trainer_name matches any gym leader name using fuzzy matching.

    Handles cases like:
        "Leader Bugsy" vs "Bugsy"
        "Surge" vs "Lt. Surge"
        "Tate&Liza" vs "Tate & Liza"
    """
    if not gym_leader_names:
        return False

    # Extract base name (strips "Leader " prefix and trailing numbers).
    base = _extract_base_name(trainer_name)

    # Exact match against gym leader names.
    if base in gym_leader_names:
        return True

    # Also try the full lowered name (without prefix stripping).
    name_lower = re.sub(r"\s+\d+$", "", trainer_name.strip().lower())
    if name_lower in gym_leader_names:
        return True

    # Fuzzy matching: check if any gym leader name is sufficiently similar.
    for gym_name in gym_leader_names:
        # Check if either contains the other (handles "Surge" in "Lt. Surge").
        if base in gym_name or gym_name in base:
            return True
        # Normalise punctuation for comparison (e.g. "tate&liza" vs "tate & liza").
        base_norm = re.sub(r"[^a-z]", "", base)
        gym_norm = re.sub(r"[^a-z]", "", gym_name)
        if base_norm == gym_norm:
            return True
        # SequenceMatcher for remaining edge cases.
        if SequenceMatcher(None, base, gym_name).ratio() >= 0.8:
            return True

    return False


def _lookup_notable_trainer(
    trainer_name: str,
    game_names: tuple[str, ...],
) -> str | None:
    """
    Look up the trainer in NOTABLE_TRAINERS for the given game.
    Returns the importance reason string, or None if not found.
    """
    notable = NOTABLE_TRAINERS.get(game_names)
    if not notable:
        return None

    base = _extract_base_name(trainer_name)

    # Direct base name lookup.
    reason = notable.get(base)
    if reason:
        return reason

    # Also try the full lowered name with just trailing numbers stripped,
    # to match entries like "rocket exec".
    name_stripped = re.sub(r"\s+\d+$", "", trainer_name.strip().lower())
    reason = notable.get(name_stripped)
    if reason:
        return reason

    return None


def classify_importance(
    trainer_name: str,
    location: str,
    gym_leader_names: set[str],
    game_names: tuple[str, ...] = (),
) -> tuple[str | None, bool]:
    """
    Classify a trainer's importance based on role.

    Args:
        trainer_name: The trainer's name from JSON
        location: The trainer's location from JSON
        gym_leader_names: Set of known gym leader names (lowercased) from Gym table
        game_names: Tuple of game names (e.g. ("diamond", "pearl")) for
                    notable trainer lookup

    Returns:
        (importance_reason, is_important) tuple
    """
    name_lower = trainer_name.lower()
    location_lower = location.lower()

    # 1. Rival keyword in name
    if any(kw in name_lower for kw in RIVAL_KEYWORDS):
        return ("rival", True)

    # 2. Champion keyword in name or location
    if any(kw in name_lower for kw in CHAMPION_KEYWORDS) or any(
        kw in location_lower for kw in CHAMPION_KEYWORDS
    ):
        return ("champion", True)

    # 3. Elite Four — check both name and location
    if any(kw in name_lower for kw in ELITE_FOUR_KEYWORDS) or any(
        kw in location_lower for kw in ELITE_FOUR_KEYWORDS
    ):
        return ("elite_four", True)

    # 4. Gym leader — fuzzy match against Gym table names
    if _fuzzy_match_gym_leader(trainer_name, gym_leader_names):
        return ("gym_leader", True)

    # 5. Evil team (pattern match) — team name + role keyword
    has_team_name = any(team in name_lower for team in EVIL_TEAM_NAMES)
    has_role = any(role in name_lower for role in EVIL_ROLE_KEYWORDS)
    if has_team_name and has_role:
        return ("evil_team_leader", True)

    # 6. Notable trainer (hardcoded per-game lookup)
    if game_names:
        notable_reason = _lookup_notable_trainer(trainer_name, game_names)
        if notable_reason:
            return (notable_reason, True)

    return (None, False)


def detect_level_outliers(
    trainer_levels: list[dict],
    window: int = 3,
    threshold: float = 1.2,
) -> set[int]:
    """
    Detect trainers whose average pokemon level is an outlier
    compared to nearby trainers (+-window in battle_order).

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
