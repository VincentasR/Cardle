def extract_variant_designers(
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw designer information from the Wikipedia infobox.

    Examples:
        "Paul Bracq"
        "Claus Luthe"
        "Chris Bangle"

    The raw string is preserved as-is.
    Canonicalization can later split multiple designers,
    remove footnote markers, and create Designer nodes.
    """

    if not variants:
        return []

    designer = None

    for key, value in infobox.items():
        normalized_key = key.strip().casefold()

        if normalized_key in {
            "designer",
            "designers",
        }:
            designer = value
            break

    if not designer:
        return []

    return [
        {
            "variant": variant,
            "designer": designer,
        }
        for variant in variants
    ]