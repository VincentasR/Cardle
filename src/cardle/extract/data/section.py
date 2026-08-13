from __future__ import annotations

from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag


HEADING_NAMES = {
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def heading_level(heading: Tag) -> int:
    """Convert h2, h3, etc. into numeric levels."""
    return int(heading.name[1])


def page_title_contains_code(
    soup: BeautifulSoup,
    variant_codes: list[str],
) -> bool:
    """
    Check whether the Wikipedia article title already identifies
    the requested generation.

    Examples:
        BMW 6 Series (E63) -> matches E63
        BMW X3             -> does not match G01
    """

    if soup.title is None:
        return False

    title = normalize_text(
        soup.title.get_text(" ", strip=True)
    )

    return any(
        normalize_text(code) in title
        for code in variant_codes
    )


def heading_contains_code(
    heading: Tag,
    variant_codes: list[str],
) -> bool:
    """Check whether a heading contains any requested variant code."""

    heading_text = normalize_text(
        heading.get_text(" ", strip=True)
    )

    return any(
        normalize_text(code) in heading_text
        for code in variant_codes
    )


def find_generation_heading(
    soup: BeautifulSoup,
    variant_codes: list[str],
) -> Tag | None:
    """Find the first heading containing a requested variant code."""

    for heading in soup.find_all(
        ["h2", "h3", "h4", "h5", "h6"]
    ):
        if heading_contains_code(
            heading,
            variant_codes,
        ):
            return heading

    return None


def get_url_fragment(
    url: str | None,
) -> str | None:
    """
    Extract and decode the fragment from a Wikipedia URL.

    Examples:
        ...BMW_303#309
            -> "309"

        ...BMW_New_Class#New_Class_Coupés
            -> "New Class Coupés"
    """

    if not url:
        return None

    fragment = urlparse(url).fragment

    if not fragment:
        return None

    fragment = unquote(fragment)

    # Wikipedia uses underscores as spaces in section fragments.
    fragment = fragment.replace("_", " ")

    return fragment.strip()


def find_fragment_heading(
    soup: BeautifulSoup,
    fragment: str,
) -> Tag | None:
    """
    Find the heading corresponding to a URL fragment.

    We first try exact normalized heading text, then fall back
    to containment for slightly different Wikipedia headings.
    """

    normalized_fragment = normalize_text(fragment)

    headings = soup.find_all(
        ["h2", "h3", "h4", "h5", "h6"]
    )

    # Prefer exact match.
    for heading in headings:
        heading_text = normalize_text(
            heading.get_text(" ", strip=True)
        )

        if heading_text == normalized_fragment:
            return heading

    # Fallback for headings with extra text.
    for heading in headings:
        heading_text = normalize_text(
            heading.get_text(" ", strip=True)
        )

        if normalized_fragment in heading_text:
            return heading

    return None


def build_section_from_heading(
    start_heading: Tag,
) -> BeautifulSoup:
    """
    Build a BeautifulSoup object containing only the section that
    starts at the supplied heading.

    Prefer Wikipedia's <section> wrapper when available.
    Otherwise collect siblings until a heading of the same or
    higher level is reached.
    """

    section_container = start_heading.find_parent("section")

    if section_container is not None:
        return BeautifulSoup(
            str(section_container),
            "html.parser",
        )

    start_level = heading_level(start_heading)

    fragment_html: list[str] = [
        str(start_heading)
    ]

    current = start_heading.find_next_sibling()

    while current is not None:
        if (
            isinstance(current, Tag)
            and current.name in HEADING_NAMES
            and heading_level(current) <= start_level
        ):
            break

        fragment_html.append(str(current))
        current = current.find_next_sibling()

    return BeautifulSoup(
        "".join(fragment_html),
        "html.parser",
    )


def extract_section(
    soup: BeautifulSoup,
    variant_codes: list[str],
    url: str | None = None,
) -> BeautifulSoup:
    """
    Return the relevant Wikipedia scope.

    Priority:

    1. URL fragment:
        BMW_303#309
            -> only the 309 section

        BMW_New_Class#New_Class_Coupés
            -> only the New Class Coupés section

    2. Dedicated generation page:
        BMW_6_Series_(E63)
            -> entire page

    3. Generation section on combined page:
        BMW_X3, requested G01
            -> only the G01 section

    4. Nothing found:
            -> entire page
    """

    # ---------------------------------------------------------
    # 1. URL FRAGMENT HAS HIGHEST PRIORITY
    # ---------------------------------------------------------

    fragment = get_url_fragment(url)

    if fragment is not None:
        fragment_heading = find_fragment_heading(
            soup,
            fragment,
        )

        if fragment_heading is not None:
            return build_section_from_heading(
                fragment_heading
            )

    # ---------------------------------------------------------
    # 2. DEDICATED GENERATION PAGE
    # ---------------------------------------------------------

    if page_title_contains_code(
        soup,
        variant_codes,
    ):
        return soup

    # ---------------------------------------------------------
    # 3. GENERATION SECTION ON A COMBINED PAGE
    # ---------------------------------------------------------

    start_heading = find_generation_heading(
        soup,
        variant_codes,
    )

    if start_heading is not None:
        return build_section_from_heading(
            start_heading
        )

    # ---------------------------------------------------------
    # 4. FALLBACK
    # ---------------------------------------------------------

    return soup


if __name__ == "__main__":
    from cardle.extract.data.fetch import fetch_page

    url = (
        "https://en.wikipedia.org/wiki/"
        "BMW_New_Class#New_Class_Coupés"
    )

    soup = fetch_page(url)

    section = extract_section(
        soup=soup,
        variant_codes=[],
        url=url,
    )

    print("SCOPED HEADINGS:")

    for heading in section.find_all(
        ["h2", "h3", "h4", "h5", "h6"]
    ):
        print(
            heading.name,
            heading.get_text(" ", strip=True),
        )