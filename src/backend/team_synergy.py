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