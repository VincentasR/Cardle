def extract_variant_lineage(
    infobox: dict[str, str],
    variants: list[str],
) -> dict[str, list[dict[str, str]]]:
    """
    Extract raw predecessor/successor information from the Wikipedia infobox.

    The raw strings are preserved for later canonicalization.

    Example:
        predecessor = "BMW E3"
        successor = "BMW 7 Series (E32)"

    Later canonicalization can:
        - remove "BMW"
        - resolve model names to variant IDs
        - create SUCCEEDED_BY relationships
        - handle multiple predecessors/successors
    """

    if not variants:
        return {
            "variant_predecessors": [],
            "variant_successors": [],
        }

    predecessor = None
    successor = None

    for key, value in infobox.items():
        normalized_key = key.strip().casefold()

        if normalized_key in {
            "predecessor",
            "predecessors",
        }:
            predecessor = value

        elif normalized_key in {
            "successor",
            "successors",
        }:
            successor = value

    variant_predecessors = []
    variant_successors = []

    if predecessor:
        variant_predecessors = [
            {
                "variant": variant,
                "predecessor": predecessor,
            }
            for variant in variants
        ]

    if successor:
        variant_successors = [
            {
                "variant": variant,
                "successor": successor,
            }
            for variant in variants
        ]

    return {
        "variant_predecessors": variant_predecessors,
        "variant_successors": variant_successors,
    }