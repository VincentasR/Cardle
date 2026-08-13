def extract_variant_vehicle_classes(
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw vehicle-class information from the Wikipedia infobox.

    Examples:
        "Compact executive car"
        "Executive car"
        "Grand tourer"
        "Subcompact crossover SUV"

    Canonicalization will later normalize these into Cardle classes.
    """

    if not variants:
        return []

    vehicle_class = None

    for key, value in infobox.items():
        normalized_key = key.strip().casefold()

        if normalized_key in {
            "class",
            "vehicle class",
        }:
            vehicle_class = value
            break

    if not vehicle_class:
        return []

    return [
        {
            "variant": variant,
            "vehicle_class": vehicle_class,
        }
        for variant in variants
    ]