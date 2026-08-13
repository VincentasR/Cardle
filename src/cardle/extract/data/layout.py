def extract_variant_layouts(
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw layout information from the Wikipedia infobox.

    Examples:
        "Front-engine, rear-wheel-drive"
        "Front-engine, all-wheel-drive"

    Canonicalization will later split this into things such as:
        engine_position = "Front"
        drivetrain = "RWD"

    or:
        engine_position = "Front"
        drivetrain = "AWD"
    """

    if not variants:
        return []

    layout = None

    for key, value in infobox.items():
        normalized_key = key.strip().casefold()

        if normalized_key in {
            "layout",
            "layouts",
        }:
            layout = value
            break

    if not layout:
        return []

    return [
        {
            "variant": variant,
            "layout": layout,
        }
        for variant in variants
    ]