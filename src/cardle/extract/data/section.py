from __future__ import annotations

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


def extract_section(
    soup: BeautifulSoup,
    variant_codes: list[str],
) -> BeautifulSoup:
    """
    Return the relevant generation scope.

    Dedicated generation page:
        BMW 6 Series (E63)
        -> return the entire page

    Combined model page:
        BMW X3, requested G01
        -> return only the G01 generation section
    """

    # If the article title already identifies the generation,
    # this is a dedicated generation page.
    if page_title_contains_code(
        soup,
        variant_codes,
    ):
        return soup

    start_heading = find_generation_heading(
        soup,
        variant_codes,
    )

    # No generation heading found: keep the entire page.
    if start_heading is None:
        return soup

    section_container = start_heading.find_parent("section")

    if section_container is not None:
        return BeautifulSoup(
            str(section_container),
            "html.parser",
        )

    # Fallback for HTML without section wrappers.
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
if __name__ == "__main__":
    from cardle.extract.data.fetch import fetch_page

    soup = fetch_page(
        "https://en.wikipedia.org/wiki/BMW_X3"
    )

    section = extract_section(
        soup,
        variant_codes=["G01"],
    )

    print("HEADINGS FOUND:")

    for heading in section.find_all(
        ["h2", "h3", "h4", "h5", "h6"]
    ):
        print(
            heading.name,
            heading.get_text(" ", strip=True),
        )