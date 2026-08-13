def extract_variant_body_styles(
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw body-style information from the Wikipedia infobox.

    This stays unnormalized for now.

    Examples:
        "2-door coupé"
        "4-door sedan"
        "5-door station wagon"

    Canonicalization will later map these to Cardle body styles such as:
        Coupe
        Sedan
        Wagon
        Convertible
        SUV
    """

    if not variants:
        return []

    body_style = None

    for key, value in infobox.items():
        normalized_key = key.strip().casefold()

        if normalized_key in {
            "body style",
            "body styles",
        }:
            body_style = value
            break

    if not body_style:
        return []

    return [
        {
            "variant": variant,
            "body_style": body_style,
        }
        for variant in variants
    ]