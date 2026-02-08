RELATION_KEYS = [
    "double_damage_to",
    "half_damage_to",
    "no_damage_to",
    "double_damage_from",
    "half_damage_from",
    "no_damage_from",
]


def _get_type_field(type_row, field_name, default=None):
    if isinstance(type_row, dict):
        return type_row.get(field_name, default)
    return getattr(type_row, field_name, default)


def _normalize_relations(relations):
    result = {}
    for key in RELATION_KEYS:
        result[key] = [item["name"] for item in relations.get(key, [])]
    return result


def _select_damage_relations(type_row, generation):
    past_relations = _get_type_field(type_row, "past_damage_relations", []) or []
    for past in past_relations:
        if int(generation) <= int(past.get("on_and_backwards", 0)):
            relations = past.copy()
            relations.pop("on_and_backwards", None)
            return _normalize_relations(relations)
    relations = _get_type_field(type_row, "current_damage_relations", {})
    return _normalize_relations(relations)


def _flatten_team_types(team):
    flattened = []
    for pokemon_types in team:
        for type_name in pokemon_types:
            flattened.append(str(type_name).lower())
    return flattened


def _compute_offense_score(attacking_types, defending_types, relations_map):
    score = 0.0
    for atk_type in attacking_types:
        relations = relations_map[atk_type]
        for def_type in defending_types:
            if def_type in relations["double_damage_to"]:
                score += 1.0
            elif def_type in relations["half_damage_to"]:
                score -= 0.5
            elif def_type in relations["no_damage_to"]:
                score -= 1.0
    return score


def score_team_matchup(team1, team2, generation, types_data):
    type_map = {}
    for type_row in types_data:
        type_name = _get_type_field(type_row, "type_name")
        intro_gen = int(_get_type_field(type_row, "generation_introduction", 0))
        if type_name and intro_gen <= int(generation):
            type_map[str(type_name).lower()] = type_row

    team1_types = [t for t in _flatten_team_types(team1) if t in type_map]
    team2_types = [t for t in _flatten_team_types(team2) if t in type_map]

    relations_used = {}
    for type_name in set(team1_types + team2_types):
        relations_used[type_name] = _select_damage_relations(type_map[type_name], generation)

    team1_offense = _compute_offense_score(team1_types, team2_types, relations_used)
    team2_offense = _compute_offense_score(team2_types, team1_types, relations_used)
    net_advantage = team1_offense - team2_offense

    pair_count = max(len(team1_types) * len(team2_types), 1)
    normalized = net_advantage / (pair_count * 2.0)
    normalized = max(min(normalized, 1.0), -1.0)
    score_percent = int(round(50 + (normalized * 50)))

    return {
        "score_percent": score_percent,
        "breakdown": {
            "team1_offense": team1_offense,
            "team2_offense": team2_offense,
            "net_advantage": net_advantage,
            "pair_count": pair_count,
        },
        "meta": {
            "relations_used": relations_used
        }
    }


def team_diversity_coverage(team, generation, types_data):
    type_map = {}
    for type_row in types_data:
        type_name = _get_type_field(type_row, "type_name")
        intro_gen = int(_get_type_field(type_row, "generation_introduction", 0))
        if type_name and intro_gen <= int(generation):
            type_map[str(type_name).lower()] = type_row

    team_types = [t for t in _flatten_team_types(team) if t in type_map]
    relations_by_type = {
        type_name: _select_damage_relations(type_row, generation)
        for type_name, type_row in type_map.items()
    }

    coverage = {}
    for target_type in sorted(type_map.keys()):
        offense = {
            "double_to": 0,
            "half_to": 0,
            "no_to": 0,
            "neutral_to": 0,
        }
        defense = {
            "double_from": 0,
            "half_from": 0,
            "no_from": 0,
            "neutral_from": 0,
        }

        for team_type in team_types:
            relations = relations_by_type[team_type]
            if target_type in relations["double_damage_to"]:
                offense["double_to"] += 1
            elif target_type in relations["half_damage_to"]:
                offense["half_to"] += 1
            elif target_type in relations["no_damage_to"]:
                offense["no_to"] += 1
            else:
                offense["neutral_to"] += 1

            if target_type in relations["double_damage_from"]:
                defense["double_from"] += 1
            elif target_type in relations["half_damage_from"]:
                defense["half_from"] += 1
            elif target_type in relations["no_damage_from"]:
                defense["no_from"] += 1
            else:
                defense["neutral_from"] += 1

        coverage[target_type] = {
            "offense": offense,
            "defense": defense,
        }

    return {
        "generation": int(generation),
        "team_types": team_types,
        "coverage": coverage,
    }


def _apply_multiplier(double_count, half_count, no_count):
    if no_count > 0:
        return 0.0
    multiplier = 1.0
    if double_count:
        multiplier *= 2 ** double_count
    if half_count:
        multiplier *= 0.5 ** half_count
    return multiplier


def _normalize_team_entries(team):
    normalized = []
    for idx, entry in enumerate(team):
        if isinstance(entry, dict):
            name = entry.get("name") or entry.get("nickname") or f"member-{idx + 1}"
            types = entry.get("types", [])
        else:
            name = f"member-{idx + 1}"
            types = entry
        normalized.append({
            "name": str(name),
            "types": [str(type_name).lower() for type_name in types],
        })
    return normalized


def summarize_team_coverage(team, generation, types_data):
    type_map = {}
    for type_row in types_data:
        type_name = _get_type_field(type_row, "type_name")
        intro_gen = int(_get_type_field(type_row, "generation_introduction", 0))
        if type_name and intro_gen <= int(generation):
            type_map[str(type_name).lower()] = type_row

    team_entries = _normalize_team_entries(team)
    filtered_team_entries = []
    for entry in team_entries:
        filtered_types = [t for t in entry["types"] if t in type_map]
        if filtered_types:
            filtered_team_entries.append({
                "name": entry["name"],
                "types": filtered_types,
            })

    team_types = [t for entry in filtered_team_entries for t in entry["types"]]
    relations_by_type = {
        type_name: _select_damage_relations(type_row, generation)
        for type_name, type_row in type_map.items()
    }

    coverage = {}
    for target_type in sorted(type_map.keys()):
        offense = {
            "double_to": 0,
            "half_to": 0,
            "no_to": 0,
        }
        defense = {
            "double_from": 0,
            "half_from": 0,
            "no_from": 0,
        }

        for team_type in team_types:
            relations = relations_by_type[team_type]
            if target_type in relations["double_damage_to"]:
                offense["double_to"] += 1
            elif target_type in relations["half_damage_to"]:
                offense["half_to"] += 1
            elif target_type in relations["no_damage_to"]:
                offense["no_to"] += 1

            if target_type in relations["double_damage_from"]:
                defense["double_from"] += 1
            elif target_type in relations["half_damage_from"]:
                defense["half_from"] += 1
            elif target_type in relations["no_damage_from"]:
                defense["no_from"] += 1

        coverage[target_type] = {
            "offense": offense,
            "defense": defense,
        }

    offense_strengths = []
    offense_weaknesses = []
    offense_immunities = []
    defense_strengths = []
    defense_weaknesses = []
    defense_immunities = []

    for target_type in sorted(coverage.keys()):
        offense = coverage[target_type]["offense"]
        defense = coverage[target_type]["defense"]

        offense_double_contributors = []
        offense_half_contributors = []
        offense_no_contributors = []
        defense_double_contributors = []
        defense_half_contributors = []
        defense_no_contributors = []

        for entry in filtered_team_entries:
            name = entry["name"]
            entry_types = entry["types"]
            if any(target_type in relations_by_type[t]["double_damage_to"] for t in entry_types):
                offense_double_contributors.append(name)
            if any(target_type in relations_by_type[t]["half_damage_to"] for t in entry_types):
                offense_half_contributors.append(name)
            if any(target_type in relations_by_type[t]["no_damage_to"] for t in entry_types):
                offense_no_contributors.append(name)

            if any(target_type in relations_by_type[t]["double_damage_from"] for t in entry_types):
                defense_double_contributors.append(name)
            if any(target_type in relations_by_type[t]["half_damage_from"] for t in entry_types):
                defense_half_contributors.append(name)
            if any(target_type in relations_by_type[t]["no_damage_from"] for t in entry_types):
                defense_no_contributors.append(name)

        offense_multiplier = _apply_multiplier(
            offense["double_to"],
            offense["half_to"],
            offense["no_to"],
        )
        defense_multiplier = _apply_multiplier(
            defense["double_from"],
            defense["half_from"],
            defense["no_from"],
        )

        if offense_multiplier == 0.0:
            offense_immunities.append({
                "type": target_type,
                "multiplier": offense_multiplier,
                "contributors": offense_no_contributors,
            })
        elif offense_multiplier > 1.0:
            offense_strengths.append({
                "type": target_type,
                "multiplier": offense_multiplier,
                "contributors": offense_double_contributors,
            })
        elif offense_multiplier < 1.0:
            offense_weaknesses.append({
                "type": target_type,
                "multiplier": offense_multiplier,
                "contributors": offense_half_contributors,
            })

        if defense_multiplier == 0.0:
            defense_immunities.append({
                "type": target_type,
                "multiplier": defense_multiplier,
                "contributors": defense_no_contributors,
            })
        elif defense_multiplier > 1.0:
            defense_weaknesses.append({
                "type": target_type,
                "multiplier": defense_multiplier,
                "contributors": defense_double_contributors,
            })
        elif defense_multiplier < 1.0:
            defense_strengths.append({
                "type": target_type,
                "multiplier": defense_multiplier,
                "contributors": defense_half_contributors,
            })

    return {
        "generation": int(generation),
        "team_types": team_types,
        "offense": {
            "strengths": offense_strengths,
            "weaknesses": offense_weaknesses,
            "immunities": offense_immunities,
        },
        "defense": {
            "strengths": defense_strengths,
            "weaknesses": defense_weaknesses,
            "immunities": defense_immunities,
        },
    }