import re

def extract_variant_production(
    soup,
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    if not variants:
        return []

    if soup.title is None:
        return []

    title = soup.title.get_text(
        " ",
        strip=True,
    )

    # Only trust page-level production when the article itself
    # identifies the requested variant/generation.
    if not any(
        variant.casefold() in title.casefold()
        for variant in variants
    ):
        return []

    production = None

    for key, value in infobox.items():
        if key.strip().casefold() == "production":
            production = value
            break

    if not production:
        return []
    if not re.search(r"\b(18|19|20)\d{2}\b", production):
        return []
    return [
        {
            "variant": variant,
            "production": production,
        }
        for variant in variants
    ]