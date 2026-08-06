import re

from bs4 import BeautifulSoup


def get_page_title(soup: BeautifulSoup) -> str | None:
    """Return the Wikipedia article title without the Wikipedia suffix."""

    if soup.title is None:
        return None

    title = soup.title.get_text(" ", strip=True)

    return title.removesuffix(" - Wikipedia").strip()


def remove_manufacturer_prefix(
    title: str,
    manufacturer: str,
) -> str:
    """
    Remove the manufacturer from the beginning of a title.

    Example:
        BMW 507 -> 507
    """

    if title.casefold().startswith(manufacturer.casefold()):
        return title[len(manufacturer):].strip()

    return title.strip()


def split_variant_codes(raw_value: str) -> list[str]:
    """
    Split combined variant codes.

    Examples:
        E63/E64       -> ["E63", "E64"]
        F12/F13/F06   -> ["F12", "F13", "F06"]
        G20           -> ["G20"]
    """

    return [
        part.strip()
        for part in raw_value.split("/")
        if part.strip()
    ]


def extract_variants(
    soup: BeautifulSoup,
    manufacturer: str,
    discovery_name: str | None = None,
    model: str | None = None,
) -> list[str]:
    """
    Extract one or more variants.

    Rules:
    1. Prefer the discovery label when it contains combined variants,
       such as "6 Series (E63/E64)".
    2. Otherwise use trailing parentheses from the page title.
    3. When the entity has "No Model", use the remaining page title
       as the variant name.
    """

    candidates: list[str] = []

    if discovery_name:
        candidates.append(discovery_name)

    page_title = get_page_title(soup)

    if page_title:
        candidates.append(page_title)

    # First try parenthesized variant codes.
    for candidate in candidates:
        match = re.search(r"\(([^()]*)\)\s*$", candidate)

        if match is None:
            continue

        raw_variant = match.group(1).strip()

        # Avoid interpreting descriptive labels as chassis codes.
        if raw_variant.casefold() in {
            "sedan",
            "sedans",
            "coupé",
            "coupés",
            "coupe",
            "coupes",
        }:
            continue

        variants = split_variant_codes(raw_variant)

        if variants:
            return variants

    # If there is no separate model, the vehicle title itself is
    # treated as the variant.
    if model == "No Model":
        fallback = discovery_name

        if not fallback and page_title:
            fallback = remove_manufacturer_prefix(
                page_title,
                manufacturer,
            )

        if fallback:
            # Remove descriptive parentheses from entries such as:
            # New Class (sedans) -> New Class
            fallback = re.sub(
                r"\s+\((?:sedans?|coupés?|coupes?)\)\s*$",
                "",
                fallback,
                flags=re.IGNORECASE,
            ).strip()

            return [fallback] if fallback else []

    return []