import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from route_matching import normalize_name, jaccard_similarity, fuzzy_match_route


def test_normalize_name_strips_punctuation_and_lowercases():
    assert normalize_name("Pewter City") == "pewter city"
    assert normalize_name("Mt. Moon") == "mt moon"
    assert normalize_name("Professor Oak's Lab") == "professor oaks lab"
    assert normalize_name("Route-3") == "route 3"


def test_jaccard_similarity_exact_match():
    assert jaccard_similarity("pewter city", "pewter city") == 1.0


def test_jaccard_similarity_no_overlap():
    assert jaccard_similarity("pewter city", "cerulean cave") == 0.0


def test_jaccard_similarity_partial_overlap():
    score = jaccard_similarity("viridian city", "viridian forest")
    assert 0.3 < score < 0.7


def test_fuzzy_match_route_exact():
    routes = [("pewter-city", 1), ("cerulean-city", 2)]
    assert fuzzy_match_route("Pewter City", routes) == 1


def test_fuzzy_match_route_substring_fallback():
    routes = [("professor-oaks-lab", 1), ("pallet-town", 2)]
    assert fuzzy_match_route("Lab", routes) == 1


def test_fuzzy_match_route_no_match():
    routes = [("pewter-city", 1), ("cerulean-city", 2)]
    assert fuzzy_match_route("Unknown Place", routes) is None
