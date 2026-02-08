STAT_KEYS = ("hp", "attack", "defense", "special_attack", "special_defense", "speed")

IV_ALIASES = {
    "hp": "hp",
    "atk": "attack",
    "attack": "attack",
    "def": "defense",
    "defense": "defense",
    "spa": "special_attack",
    "sp_atk": "special_attack",
    "special_attack": "special_attack",
    "spd": "special_defense",
    "sp_def": "special_defense",
    "special_defense": "special_defense",
    "spe": "speed",
    "speed": "speed",
}

DV_ALIASES = {
    "hp": "hp",
    "at": "attack",
    "df": "defense",
    "sl": "special_attack",
    "sd": "special_defense",
    "sp": "speed",
}

NATURE_EFFECTS = {
    "Lonely": ("attack", "defense"),
    "Brave": ("attack", "speed"),
    "Adamant": ("attack", "special_attack"),
    "Naughty": ("attack", "special_defense"),
    "Bold": ("defense", "attack"),
    "Relaxed": ("defense", "speed"),
    "Impish": ("defense", "special_attack"),
    "Lax": ("defense", "special_defense"),
    "Timid": ("speed", "attack"),
    "Hasty": ("speed", "defense"),
    "Jolly": ("speed", "special_attack"),
    "Naive": ("speed", "special_defense"),
    "Modest": ("special_attack", "attack"),
    "Mild": ("special_attack", "defense"),
    "Quiet": ("special_attack", "speed"),
    "Rash": ("special_attack", "special_defense"),
    "Calm": ("special_defense", "attack"),
    "Gentle": ("special_defense", "defense"),
    "Sassy": ("special_defense", "speed"),
    "Careful": ("special_defense", "special_attack"),
}


def _extract_iv_payload(ivs):
    if isinstance(ivs, dict):
        if "dvs" in ivs and isinstance(ivs["dvs"], dict):
            return ivs["dvs"]
        if "ivs" in ivs and isinstance(ivs["ivs"], dict):
            return ivs["ivs"]
    return ivs


def _normalize_ivs(ivs):
    payload = _extract_iv_payload(ivs)
    if not isinstance(payload, dict):
        raise ValueError("IVs/DVs must be provided as a dict.")

    dv_only_keys = {"at", "df", "sl", "sd", "sp"}
    is_dv_format = any(key in dv_only_keys for key in payload.keys())
    aliases = DV_ALIASES if is_dv_format else IV_ALIASES
    normalized = {stat: 0 for stat in STAT_KEYS}

    for key, value in payload.items():
        if key not in aliases:
            continue
        stat_key = aliases[key]
        try:
            stat_value = int(value)
        except (TypeError, ValueError):
            continue
        if is_dv_format:
            stat_value = max(0, min(15, stat_value)) * 2
        else:
            stat_value = max(0, min(31, stat_value))
        normalized[stat_key] = stat_value

    return normalized


def _normalize_nature_name(nature):
    if nature is None:
        return None
    if hasattr(nature, "value"):
        return str(nature.value)
    return str(nature)


def _nature_multiplier(nature, stat_key):
    if stat_key == "hp":
        return 1.0
    nature_name = _normalize_nature_name(nature)
    if not nature_name:
        return 1.0
    effect = NATURE_EFFECTS.get(nature_name)
    if not effect:
        return 1.0
    increase, decrease = effect
    if stat_key == increase:
        return 1.1
    if stat_key == decrease:
        return 0.9
    return 1.0


def _calculate_stat(base, iv, level, nature_modifier=1.0, is_hp=False, ev=0):
    if is_hp:
        return ((2 * base + iv + ev // 4) * level) // 100 + level + 10
    base_stat = ((2 * base + iv + ev // 4) * level) // 100 + 5
    return int(base_stat * nature_modifier)


def calculate_true_stats(all_pokemon, owned_pokemon, ivs):
    """Calculate true stats assuming EVs are zero."""
    normalized_ivs = _normalize_ivs(ivs)
    level = owned_pokemon.level
    nature = owned_pokemon.nature

    base_stats = {
        "hp": all_pokemon.base_hp,
        "attack": all_pokemon.base_attack,
        "defense": all_pokemon.base_defense,
        "special_attack": all_pokemon.base_special_attack,
        "special_defense": all_pokemon.base_special_defense,
        "speed": all_pokemon.base_speed,
    }

    stats = {}
    for stat_key in STAT_KEYS:
        nature_modifier = _nature_multiplier(nature, stat_key)
        stats[stat_key] = _calculate_stat(
            base_stats[stat_key],
            normalized_ivs[stat_key],
            level,
            nature_modifier=nature_modifier,
            is_hp=stat_key == "hp",
            ev=0,
        )

    return stats


def _find_ev_for_stat(base, iv, level, nature_modifier, is_hp, target_stat):
    for ev in range(0, 253):
        if _calculate_stat(base, iv, level, nature_modifier, is_hp=is_hp, ev=ev) == target_stat:
            return ev

    best_ev = 0
    best_delta = None
    for ev in range(0, 253):
        stat_value = _calculate_stat(base, iv, level, nature_modifier, is_hp=is_hp, ev=ev)
        delta = abs(stat_value - target_stat)
        if best_delta is None or delta < best_delta:
            best_ev = ev
            best_delta = delta
    return best_ev


def calculate_evs_from_stats(all_pokemon, owned_pokemon, ivs, true_stats):
    """Calculate EVs per stat, clamped to 0-252."""
    normalized_ivs = _normalize_ivs(ivs)
    level = owned_pokemon.level
    nature = owned_pokemon.nature

    base_stats = {
        "hp": all_pokemon.base_hp,
        "attack": all_pokemon.base_attack,
        "defense": all_pokemon.base_defense,
        "special_attack": all_pokemon.base_special_attack,
        "special_defense": all_pokemon.base_special_defense,
        "speed": all_pokemon.base_speed,
    }

    evs = {}
    for stat_key in STAT_KEYS:
        if stat_key not in true_stats:
            continue
        nature_modifier = _nature_multiplier(nature, stat_key)
        ev_value = _find_ev_for_stat(
            base_stats[stat_key],
            normalized_ivs[stat_key],
            level,
            nature_modifier,
            stat_key == "hp",
            true_stats[stat_key],
        )
        evs[stat_key] = max(0, min(252, ev_value))

    return evs

