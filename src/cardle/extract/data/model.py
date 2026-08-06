import re

from bs4 import BeautifulSoup


NO_MODEL = "No Model"


def get_page_title(soup: BeautifulSoup) -> str | None:
    """
    Extract the Wikipedia article title.

    Example:
        "BMW 1 Series (F70) - Wikipedia"
        becomes
        "BMW 1 Series (F70)"
    """

    if soup.title is None:
        return None

    title = soup.title.get_text(" ", strip=True)

    return title.removesuffix(" - Wikipedia").strip()


def extract_model(
    soup: BeautifulSoup,
    manufacturer: str,
) -> str:
    """
    Extract the model name from a generation-page title.

    Examples:
        BMW 1 Series (F70) -> 1 Series
        BMW 6 Series (E24) -> 6 Series
        BMW X3 (G45)       -> X3
        BMW E9             -> No Model

    A title without trailing parentheses is currently treated as a
    vehicle without a separate model entity.
    """

    title = get_page_title(soup)

    if title is None:
        return NO_MODEL

    # Match a trailing parenthesized designation such as:
    # (F70), (E24), (G45), (XX50)
    match = re.search(r"\s+\(([^()]*)\)\s*$", title)

    if match is None:
        return NO_MODEL

    # Remove the trailing variant code.
    title_without_variant = title[:match.start()].strip()

    # Remove the manufacturer only when it appears at the start.
    if title_without_variant.casefold().startswith(
        manufacturer.casefold()
    ):
        model = title_without_variant[len(manufacturer):].strip()
    else:
        model = title_without_variant

    return model or NO_MODEL