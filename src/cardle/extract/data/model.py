import re

from bs4 import BeautifulSoup


NO_MODEL = "No Model"


def get_page_title(soup: BeautifulSoup) -> str | None:
    if soup.title is None:
        return None

    title = soup.title.get_text(" ", strip=True)

    return title.removesuffix(" - Wikipedia").strip()


def remove_manufacturer_prefix(
    text: str,
    manufacturer: str,
) -> str:
    if text.casefold().startswith(manufacturer.casefold()):
        return text[len(manufacturer):].strip()

    return text.strip()


def extract_parenthesized_part(text: str) -> str | None:
    match = re.search(r"\(([^()]*)\)\s*$", text)

    if match is None:
        return None

    return match.group(1).strip()


def remove_trailing_parentheses(text: str) -> str:
    return re.sub(
        r"\s*\([^()]*\)\s*$",
        "",
        text,
    ).strip()


def looks_like_variant_code(value: str) -> bool:
    """
    Roughly recognize chassis/generation codes.

    Examples:
        U10
        F74
        G01
        E24
        XX50
    """

    return bool(
        re.fullmatch(
            r"[A-Z]{1,3}\d{1,3}[A-Z0-9]*",
            value.strip(),
            flags=re.IGNORECASE,
        )
    )


def page_has_generation_section(
    soup: BeautifulSoup,
    variant_code: str,
) -> bool:
    """
    Check whether the page contains a heading for the requested variant.

    Example:
        BMW X2 page
        -> "Second generation (U10; 2023)"
    """

    code = variant_code.casefold()

    for heading in soup.find_all(
        ["h2", "h3", "h4", "h5", "h6"]
    ):
        text = heading.get_text(
            " ",
            strip=True,
        ).casefold()

        if code in text:
            return True

    return False


def extract_model(
    soup: BeautifulSoup,
    manufacturer: str,
    discovery_name: str | None = None,
) -> str:
    """
    Extract the canonical model.

    Examples:

        discovery: 6 Series (E63/E64)
        page: BMW 6 Series (E63)
        -> 6 Series

        discovery: X3 (G01)
        page: BMW X3
        -> X3

        discovery: U10
        page: BMW X2
        section: Second generation (U10; 2023)
        -> X2

        discovery: F74
        page: BMW 2 Series Gran Coupé
        section: Second generation (F74/F78; 2025)
        -> 2 Series Gran Coupé

        discovery: 507
        page: BMW 507
        -> No Model
    """

    page_title = get_page_title(soup)

    if page_title is None:
        return NO_MODEL

    title_without_manufacturer = remove_manufacturer_prefix(
        page_title,
        manufacturer,
    )

    # Case 1:
    # Discovery already contains model + variant.
    #
    # X3 (G01) -> X3
    # 6 Series (E63/E64) -> 6 Series
    if discovery_name:
        discovery_variant = extract_parenthesized_part(
            discovery_name
        )

        if discovery_variant is not None:
            model = remove_trailing_parentheses(
                discovery_name
            )

            if model:
                return model

    # Case 2:
    # Dedicated generation page.
    #
    # BMW 6 Series (E24) -> 6 Series
    title_variant = extract_parenthesized_part(
        title_without_manufacturer
    )

    if title_variant is not None:
        model = remove_trailing_parentheses(
            title_without_manufacturer
        )

        if model:
            return model

    # Case 3:
    # Discovery gave only the chassis code, while Wikipedia uses a
    # broad model page containing generation sections.
    #
    # U10 + BMW X2 -> X2
    # F74 + BMW 2 Series Gran Coupé -> 2 Series Gran Coupé
    if (
        discovery_name
        and looks_like_variant_code(discovery_name)
        and page_has_generation_section(
            soup,
            discovery_name,
        )
    ):
        return title_without_manufacturer

    # Otherwise this is something like:
    #
    # BMW 507
    # BMW 700
    # BMW 3200 CS
    #
    # where the title itself represents the variant.
    return NO_MODEL