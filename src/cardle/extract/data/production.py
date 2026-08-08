def extract_variant_production(
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw production information from the page infobox.

    This is variant-level production data.
    Canonicalization will later parse it into start_year/end_year.
    """

    if not variants:
        return []

    production = None

    for key, value in infobox.items():
        if key.strip().casefold() == "production":
            production = value
            break

    if not production:
        return []

    return [
        {
            "variant": variant,
            "production": production,
        }
        for variant in variants
    ]