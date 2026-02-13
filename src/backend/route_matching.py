import re


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation (except spaces), collapse whitespace."""
    result = name.lower()
    result = re.sub(r"[\-]", " ", result)
    result = re.sub(r"['\.]", "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two normalized strings."""
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a and not tokens_b:
        return 1.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def fuzzy_match_route(
    trainer_location: str,
    route_candidates: list[tuple[str, int]],
    threshold: float = 0.8,
) -> int | None:
    """
    Match a trainer location string to a route ID.

    Args:
        trainer_location: Raw location string from trainer JSON (e.g., "Pewter City")
        route_candidates: List of (route_name, route_id) tuples from the DB
        threshold: Minimum Jaccard score for a match (default 0.8)

    Returns:
        Matched route_id, or None if no match found.
    """
    norm_location = normalize_name(trainer_location)

    # Pass 1: Jaccard similarity >= threshold
    best_score = 0.0
    best_id = None
    for route_name, route_id in route_candidates:
        norm_route = normalize_name(route_name)
        score = jaccard_similarity(norm_location, norm_route)
        if score >= threshold and score > best_score:
            best_score = score
            best_id = route_id

    if best_id is not None:
        return best_id

    # Pass 2: Substring containment fallback
    for route_name, route_id in route_candidates:
        norm_route = normalize_name(route_name)
        if norm_location in norm_route or norm_route in norm_location:
            return route_id

    return None
