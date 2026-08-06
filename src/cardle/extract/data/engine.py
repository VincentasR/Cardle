from bs4 import BeautifulSoup

from cardle.extract.data.table.parser import (
    expand_table,
    find_first_header_position,
    get_cell_text,
    is_section_heading,
    normalize_text,
)
from cardle.extract.data.table.version_table import VersionRow


ENGINE_HEADERS = {
    "engine",
    "engine code",
}


def extract_version_engines(
    rows: list[VersionRow],
) -> list[dict[str, str]]:
    """Extract Version -> Engine relationships."""

    relationships: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        if row.version is None or row.engine is None:
            continue

        pair = (
            normalize_text(row.version),
            normalize_text(row.engine),
        )

        if pair in seen:
            continue

        seen.add(pair)

        relationships.append(
            {
                "version": row.version,
                "engine": row.engine,
            }
        )

    return relationships


def extract_infobox_engines(
    infobox: dict[str, str],
) -> list[str]:
    """Extract engines listed directly in an infobox."""

    engines: list[str] = []

    for field_name, value in infobox.items():
        if normalize_text(field_name) not in ENGINE_HEADERS:
            continue

        if value:
            engines.append(value)

    return engines


def extract_engines_from_engine_only_tables(
    soup: BeautifulSoup,
) -> list[str]:
    """
    Extract engines from tables with an Engine column but without a
    Model or Version column.

    Such a table describes the page-level variant rather than versions.
    """

    engines: list[str] = []
    seen: set[str] = set()

    version_headers = {
        "model",
        "model name",
        "version",
    }

    for table in soup.select("table.wikitable"):
        grid = expand_table(table)

        engine_position = find_first_header_position(
            grid,
            ENGINE_HEADERS,
        )

        if engine_position is None:
            continue

        version_position = find_first_header_position(
            grid,
            version_headers,
        )

        # Tables with a version column are handled by VersionRow.
        if version_position is not None:
            continue

        header_row_index, engine_column = engine_position

        for row in grid[header_row_index + 1:]:
            if engine_column >= len(row):
                continue

            cell = row[engine_column]

            if cell is None or is_section_heading(cell):
                continue

            engine = get_cell_text(cell)

            if engine is None:
                continue

            normalized_engine = normalize_text(engine)

            if normalized_engine in seen:
                continue

            seen.add(normalized_engine)
            engines.append(engine)

    return engines


def extract_variant_engines(
    soup: BeautifulSoup,
    infobox: dict[str, str],
    variants: list[str],
    versions: list[str],
) -> list[dict[str, str]]:
    """
    Extract Variant -> Engine relationships when no versions exist.

    Variant engines can come from:
    1. A page-level infobox.
    2. An engine table without a Model/Version column.
    """

    if versions:
        return []

    if len(variants) != 1:
        return []

    engines = extract_infobox_engines(infobox)
    engines.extend(
        extract_engines_from_engine_only_tables(soup)
    )

    relationships: list[dict[str, str]] = []
    seen: set[str] = set()

    for engine in engines:
        normalized_engine = normalize_text(engine)

        if normalized_engine in seen:
            continue

        seen.add(normalized_engine)

        relationships.append(
            {
                "variant": variants[0],
                "engine": engine,
            }
        )

    return relationships