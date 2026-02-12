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
    trainer_levels = [
        {"battle_order": 0, "avg_level": 14},
        {"battle_order": 1, "avg_level": 15},
        {"battle_order": 2, "avg_level": 16},
        {"battle_order": 3, "avg_level": 30},
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
