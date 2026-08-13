import re
from collections import defaultdict


def build_variant_registry(canonical_vehicles: list[dict]) -> dict[str, list[dict]]:
    """
    Build a lookup from Wikipedia source URL to canonical variants.

    A single Wikipedia page may represent multiple Cardle variants,
    so each URL maps to a list of candidates.
    """
    registry = defaultdict(list)

    for vehicle in canonical_vehicles:
        for variant in vehicle.get("variants", []):
            source_url = variant.get("source_url")

            if not source_url:
                continue

            registry[source_url].append(
                {
                    "id": variant["id"],
                    "name": variant["name"],
                }
            )

    return dict(registry)


def _find_variant_code(text: str) -> str | None:
    """
    Try to extract a BMW-style chassis code from relationship text.

    Examples:
        "BMW 6 Series (E63)" -> "E63"
        "BMW E9" -> "E9"
        "BMW 7 Series (F01)" -> "F01"
    """
    if not text:
        return None

    matches = re.findall(
        r"\b[A-Z]{1,2}\d{1,3}\b",
        text,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    return matches[-1].upper()


def resolve_target_id(
    relationship: dict,
    registry: dict[str, list[dict]],
) -> str | None:
    """
    Resolve one predecessor/successor reference to a Cardle variant ID.
    """
    url = relationship.get("url")

    if not url:
        return None

    candidates = registry.get(url, [])

    if not candidates:
        return None

    # Easy case: the URL points to exactly one canonical variant.
    if len(candidates) == 1:
        return candidates[0]["id"]

    # Multiple variants share the same Wikipedia page.
    # Try to identify the intended one using the relationship text.
    relationship_name = relationship.get("name", "")
    target_code = _find_variant_code(relationship_name)

    if target_code:
        for candidate in candidates:
            if candidate["name"].upper() == target_code:
                return candidate["id"]

    # Ambiguous: don't guess.
    return None


def resolve_relationships(
    canonical_vehicles: list[dict],
) -> list[dict]:
    """
    Resolve predecessor and successor target IDs across
    the complete canonical dataset.
    """
    registry = build_variant_registry(canonical_vehicles)

    for vehicle in canonical_vehicles:
        for variant in vehicle.get("variants", []):

            for predecessor in variant.get("predecessors", []):
                predecessor["target_id"] = resolve_target_id(
                    predecessor,
                    registry,
                )

            for successor in variant.get("successors", []):
                successor["target_id"] = resolve_target_id(
                    successor,
                    registry,
                )

    return canonical_vehicles