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

    # Evil team leader/admin — require both a team name AND a role keyword
    has_team_name = any(team in name_lower for team in EVIL_TEAM_NAMES)
    has_role = any(role in name_lower for role in EVIL_ROLE_KEYWORDS)
    if has_team_name and has_role:
        return ("evil_team_leader", True)

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
