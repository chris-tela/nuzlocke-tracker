import os
import sys
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import calc


def _make_pokemon(base_stats, level=50, nature="Adamant"):
    all_pokemon = SimpleNamespace(
        base_hp=base_stats["hp"],
        base_attack=base_stats["attack"],
        base_defense=base_stats["defense"],
        base_special_attack=base_stats["special_attack"],
        base_special_defense=base_stats["special_defense"],
        base_speed=base_stats["speed"],
    )
    owned_pokemon = SimpleNamespace(level=level, nature=nature)
    return all_pokemon, owned_pokemon


def _calc_stat(base, iv, level, nature_modifier=1.0, is_hp=False):
    if is_hp:
        return (2 * base + iv) * level // 100 + level + 10
    base_stat = (2 * base + iv) * level // 100 + 5
    return int(base_stat * nature_modifier)


def test_calculate_true_stats_with_ivs_and_nature():
    base_stats = {
        "hp": 45,
        "attack": 49,
        "defense": 49,
        "special_attack": 65,
        "special_defense": 65,
        "speed": 45,
    }
    all_pokemon, owned_pokemon = _make_pokemon(base_stats, level=50, nature="Adamant")
    ivs = {"hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31}

    stats = calc.calculate_true_stats(all_pokemon, owned_pokemon, ivs)

    assert stats == {
        "hp": _calc_stat(45, 31, 50, is_hp=True),
        "attack": _calc_stat(49, 31, 50, nature_modifier=1.1),
        "defense": _calc_stat(49, 31, 50),
        "special_attack": _calc_stat(65, 31, 50, nature_modifier=0.9),
        "special_defense": _calc_stat(65, 31, 50),
        "speed": _calc_stat(45, 31, 50),
    }


def test_calculate_true_stats_with_dvs():
    base_stats = {
        "hp": 45,
        "attack": 49,
        "defense": 49,
        "special_attack": 65,
        "special_defense": 65,
        "speed": 45,
    }
    all_pokemon, owned_pokemon = _make_pokemon(base_stats, level=50, nature=None)
    dvs = {"hp": 8, "at": 9, "df": 8, "sl": 8, "sd": 8, "sp": 8}

    stats = calc.calculate_true_stats(all_pokemon, owned_pokemon, dvs)

    assert stats == {
        "hp": _calc_stat(45, 16, 50, is_hp=True),
        "attack": _calc_stat(49, 18, 50),
        "defense": _calc_stat(49, 16, 50),
        "special_attack": _calc_stat(65, 16, 50),
        "special_defense": _calc_stat(65, 16, 50),
        "speed": _calc_stat(45, 16, 50),
    }


def test_calculate_evs_from_stats_returns_single_value():
    base_stats = {
        "hp": 45,
        "attack": 49,
        "defense": 49,
        "special_attack": 65,
        "special_defense": 65,
        "speed": 45,
    }
    all_pokemon, owned_pokemon = _make_pokemon(base_stats, level=50, nature="Adamant")
    ivs = {"hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31}

    attack_ev = 100
    attack_stat = int(((2 * 49 + 31 + attack_ev // 4) * 50 // 100 + 5) * 1.1)
    true_stats = {
        "hp": _calc_stat(45, 31, 50, is_hp=True),
        "attack": attack_stat,
        "defense": _calc_stat(49, 31, 50),
        "special_attack": _calc_stat(65, 31, 50, nature_modifier=0.9),
        "special_defense": _calc_stat(65, 31, 50),
        "speed": _calc_stat(45, 31, 50),
    }

    evs = calc.calculate_evs_from_stats(all_pokemon, owned_pokemon, ivs, true_stats)

    assert evs["attack"] == attack_ev


test_calculate_evs_from_stats_returns_single_value()