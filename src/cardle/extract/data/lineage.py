from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag


WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"


def _normalize_key(text: str) -> str:
    return " ".join(
        text.casefold().split()
    )


def _find_infobox_row(
    soup: BeautifulSoup,
    field_names: set[str],
) -> Tag | None:
    """
    Find an infobox row for fields such as:

        Predecessor
        Successor

    Returns the <tr> containing the field.
    """

    infobox = soup.find(
        "table",
        class_=lambda classes: (
            classes
            and "infobox" in classes
        ),
    )

    if infobox is None:
        return None

    for row in infobox.find_all("tr"):
        header = row.find("th")

        if header is None:
            continue

        key = _normalize_key(
            header.get_text(
                " ",
                strip=True,
            )
        )

        if key in field_names:
            return row

    return None


def _extract_wikipedia_urls(
    row: Tag | None,
) -> list[str]:
    """
    Extract Wikipedia article URLs from an infobox row.

    Supports Wikipedia links in forms such as:

        ./BMW_E9
        /wiki/BMW_E9
        https://en.wikipedia.org/wiki/BMW_E9
    """

    if row is None:
        return []

    urls = []

    for link in row.find_all("a", href=True):
        href = link["href"].strip()

        # -----------------------------------------------------
        # Convert Wikipedia's different internal-link formats
        # into full canonical URLs.
        # -----------------------------------------------------

        if href.startswith("./"):
            article_part = href[2:]

            url = (
                "https://en.wikipedia.org/wiki/"
                + article_part
            )

        elif href.startswith("/wiki/"):
            article_part = href[len("/wiki/"):]

            url = (
                "https://en.wikipedia.org/wiki/"
                + article_part
            )

        elif href.startswith(
            "https://en.wikipedia.org/wiki/"
        ):
            article_part = href.split(
                "/wiki/",
                1,
            )[1]

            url = href

        else:
            continue

        # Ignore non-article Wikipedia namespaces:
        # File:, Help:, Special:, etc.
        if ":" in article_part:
            continue

        # Strip fragments because the canonicalization registry
        # should identify the Wikipedia article itself.
        url = url.split("#", 1)[0]

        if url not in urls:
            urls.append(url)

    return urls

def _add_urls(
    entry: dict[str, str],
    urls: list[str],
) -> dict:
    """
    Preserve the current raw relationship format while adding
    Wikipedia identifiers.

    One target:
        "url": "https://..."

    Multiple targets:
        "urls": ["https://...", "https://..."]
    """

    if len(urls) == 1:
        entry["url"] = urls[0]

    elif len(urls) > 1:
        entry["urls"] = urls

    return entry


def extract_variant_lineage(
    soup: BeautifulSoup,
    infobox: dict[str, str],
    variants: list[str],
) -> dict[str, list[dict]]:
    """
    Extract raw predecessor/successor information from the
    Wikipedia infobox.

    Existing displayed text is preserved exactly as before.

    Wikipedia URLs are additionally retained so canonicalization
    can later resolve external Wikipedia identifiers to Cardle IDs.
    """

    if not variants:
        return {
            "variant_predecessors": [],
            "variant_successors": [],
        }

    predecessor = None
    successor = None

    for key, value in infobox.items():
        normalized_key = _normalize_key(
            key
        )

        if normalized_key in {
            "predecessor",
            "predecessors",
        }:
            predecessor = value

        elif normalized_key in {
            "successor",
            "successors",
        }:
            successor = value

    # ---------------------------------------------------------
    # Recover URLs from the original HTML.
    # ---------------------------------------------------------

    predecessor_row = _find_infobox_row(
        soup,
        {
            "predecessor",
            "predecessors",
        },
    )

    successor_row = _find_infobox_row(
        soup,
        {
            "successor",
            "successors",
        },
    )

    predecessor_urls = (
        _extract_wikipedia_urls(
            predecessor_row
        )
    )

    successor_urls = (
        _extract_wikipedia_urls(
            successor_row
        )
    )

    # ---------------------------------------------------------
    # Build exactly the same raw relationship objects as before,
    # now enriched with URLs.
    # ---------------------------------------------------------

    variant_predecessors = []

    if predecessor:
        for variant in variants:
            entry = {
                "variant": variant,
                "predecessor": predecessor,
            }

            variant_predecessors.append(
                _add_urls(
                    entry,
                    predecessor_urls,
                )
            )

    variant_successors = []

    if successor:
        for variant in variants:
            entry = {
                "variant": variant,
                "successor": successor,
            }

            variant_successors.append(
                _add_urls(
                    entry,
                    successor_urls,
                )
            )

    return {
        "variant_predecessors": variant_predecessors,
        "variant_successors": variant_successors,
    }