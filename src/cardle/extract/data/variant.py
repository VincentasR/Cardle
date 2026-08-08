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
    Split combined variant codes and remove duplicates.

    Examples:
        E63/E64
        -> ["E63", "E64"]

        F12/F13/F06
        -> ["F12", "F13", "F06"]

        G14/G15/G15
        -> ["G14", "G15"]
    """

    values = [
        part.strip()
        for part in raw_value.split("/")
        if part.strip()
    ]

    return list(dict.fromkeys(values))


def looks_like_variant_code(value: str) -> bool:
    """
    Roughly recognize chassis/generation codes.

    Examples:
        E24
        F39
        G01
        U10
        F74
        G26
        XX50
    """

    return bool(
        re.fullmatch(
            r"[A-Z]{1,3}\d{1,3}[A-Z0-9]*",
            value.strip(),
            flags=re.IGNORECASE,
        )
    )


def extract_parenthesized_variants(
    value: str,
) -> list[str]:
    """
    Extract trailing parenthesized variant codes.

    Examples:
        6 Series (E63/E64)
        -> ["E63", "E64"]

        X3 (G01)
        -> ["G01"]
    """

    match = re.search(
        r"\(([^()]*)\)\s*$",
        value,
    )

    if match is None:
        return []

    raw_variant = match.group(1).strip()

    # These describe body styles rather than chassis codes.
    if raw_variant.casefold() in {
        "sedan",
        "sedans",
        "coupé",
        "coupés",
        "coupe",
        "coupes",
    }:
        return []

    return split_variant_codes(raw_variant)


def extract_variants(
    soup: BeautifulSoup,
    manufacturer: str,
    discovery_name: str | None = None,
    model: str | None = None,
) -> list[str]:
    """
    Extract one or more variants.

    Priority:

    1. Discovery name containing model + variant:
           6 Series (E63/E64)
           -> ["E63", "E64"]

    2. Discovery name containing only a chassis code:
           G26
           -> ["G26"]

       This is important when the discovered vehicle points to a
       broader Wikipedia article such as BMW 4 Series (G22).

    3. Wikipedia article title:
           BMW 6 Series (E24)
           -> ["E24"]

    4. No-model vehicles use the vehicle name itself:
           BMW 507
           -> ["507"]
    """

    page_title = get_page_title(soup)

    # ---------------------------------------------------------
    # 1. DISCOVERY INFORMATION HAS PRIORITY
    # ---------------------------------------------------------

    if discovery_name:
        # Example:
        # 6 Series (E63/E64)
        discovery_variants = extract_parenthesized_variants(
            discovery_name
        )

        if discovery_variants:
            return discovery_variants

        # Example:
        # G26
        #
        # Do this BEFORE looking at the Wikipedia title.
        if looks_like_variant_code(discovery_name):
            return [
                discovery_name.strip()
            ]

    # ---------------------------------------------------------
    # 2. FALL BACK TO THE WIKIPEDIA ARTICLE TITLE
    # ---------------------------------------------------------

    if page_title:
        page_variants = extract_parenthesized_variants(
            page_title
        )

        if page_variants:
            return page_variants

    # ---------------------------------------------------------
    # 3. NO-MODEL VEHICLES
    # ---------------------------------------------------------

    if model == "No Model":
        fallback = discovery_name

        if not fallback and page_title:
            fallback = remove_manufacturer_prefix(
                page_title,
                manufacturer,
            )

        if fallback:
            # New Class (sedans) etc. should not interpret
            # "sedans" as a chassis code.
            fallback = re.sub(
                r"\s+\((?:sedans?|coupés?|coupes?)\)\s*$",
                "",
                fallback,
                flags=re.IGNORECASE,
            ).strip()

            if fallback:
                return [fallback]

    return [] 