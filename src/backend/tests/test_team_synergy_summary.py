import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from team_synergy import summarize_team_coverage


def test_summarize_team_coverage_lists_multipliers_with_contributors():
    types_data = [
        {
            "type_name": "fire",
            "generation_introduction": 1,
            "current_damage_relations": {
                "double_damage_to": [{"name": "grass"}],
                "half_damage_to": [{"name": "water"}],
                "no_damage_to": [{"name": "ghost"}],
                "double_damage_from": [{"name": "water"}],
                "half_damage_from": [{"name": "grass"}],
                "no_damage_from": [{"name": "ghost"}],
            },
            "past_damage_relations": [],
        },
        {
            "type_name": "water",
            "generation_introduction": 1,
            "current_damage_relations": {
                "double_damage_to": [{"name": "fire"}],
                "half_damage_to": [{"name": "grass"}],
                "no_damage_to": [],
                "double_damage_from": [{"name": "grass"}],
                "half_damage_from": [{"name": "fire"}],
                "no_damage_from": [],
            },
            "past_damage_relations": [],
        },
        {
            "type_name": "grass",
            "generation_introduction": 1,
            "current_damage_relations": {
                "double_damage_to": [{"name": "water"}],
                "half_damage_to": [{"name": "fire"}],
                "no_damage_to": [],
                "double_damage_from": [{"name": "fire"}],
                "half_damage_from": [{"name": "water"}],
                "no_damage_from": [],
            },
            "past_damage_relations": [],
        },
        {
            "type_name": "ghost",
            "generation_introduction": 1,
            "current_damage_relations": {
                "double_damage_to": [],
                "half_damage_to": [],
                "no_damage_to": [{"name": "normal"}],
                "double_damage_from": [],
                "half_damage_from": [],
                "no_damage_from": [{"name": "normal"}],
            },
            "past_damage_relations": [],
        },
    ]

    summary = summarize_team_coverage(
        team=[
            {"name": "Torch", "types": ["fire"]},
            {"name": "Blaze", "types": ["fire"]},
        ],
        generation=1,
        types_data=types_data,
    )

    assert summary["offense"]["strengths"] == [
        {"type": "grass", "multiplier": 4.0, "contributors": ["Torch", "Blaze"]}
    ]
    assert summary["offense"]["weaknesses"] == [
        {"type": "water", "multiplier": 0.25, "contributors": ["Torch", "Blaze"]}
    ]
    assert summary["offense"]["immunities"] == [
        {"type": "ghost", "multiplier": 0.0, "contributors": ["Torch", "Blaze"]}
    ]
    assert summary["defense"]["strengths"] == [
        {"type": "grass", "multiplier": 0.25, "contributors": ["Torch", "Blaze"]}
    ]
    assert summary["defense"]["weaknesses"] == [
        {"type": "water", "multiplier": 4.0, "contributors": ["Torch", "Blaze"]}
    ]
    assert summary["defense"]["immunities"] == [
        {"type": "ghost", "multiplier": 0.0, "contributors": ["Torch", "Blaze"]}
    ]
