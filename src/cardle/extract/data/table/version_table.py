from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from cardle.extract.data.table.parser import (
    expand_table,
    find_first_header_position,
    get_cell_text,
    is_section_heading,
    normalize_text,
)


VERSION_HEADERS = {
    "model",
    "model name",
    "version",
}

YEAR_HEADERS = {
    "years",
    "year",
    "production",
    "production years",
}

ENGINE_HEADERS = {
    "engine",
    "engine code",
}

POWER_HEADERS = {
    "power",
    "power output",
    "output",
}


@dataclass(frozen=True)
class VersionRow:
    """
    One logical row extracted from a Wikipedia version/specification table.

    Fields remain as cleaned Wikipedia text for now. Parsing values such
    as years, horsepower, displacement, and engine codes comes later.
    """

    version: str | None
    years: str | None
    engine: str | None
    power: str | None


def find_column(
    grid: list[list[Tag | None]],
    supported_headers: set[str],
    allow_prefix: bool = False,
) -> tuple[int, int] | None:
    """
    Find the first column whose header matches a supported name.

    When allow_prefix=True, headers such as "Engine-turbo" also match
    the supported header "Engine".
    """

    normalized_headers = {
        normalize_text(header)
        for header in supported_headers
    }

    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell is None or cell.name != "th":
                continue

            value = get_cell_text(cell)

            if value is None:
                continue

            normalized_value = normalize_text(value)

            if normalized_value in normalized_headers:
                return row_index, column_index

            if allow_prefix and any(
                normalized_value.startswith(header)
                for header in normalized_headers
            ):
                return row_index, column_index

    return None


def get_row_value(
    row: list[Tag | None],
    column_index: int | None,
) -> str | None:
    """
    Extract cleaned text from one logical table column.
    """

    if column_index is None:
        return None

    if column_index >= len(row):
        return None

    cell = row[column_index]

    if cell is None:
        return None

    if is_section_heading(cell):
        return None

    return get_cell_text(cell)


def parse_version_table(
    table: Tag,
) -> list[VersionRow]:
    """
    Parse one Wikipedia table containing vehicle-version information.

    A usable version table must contain a version-like column such as
    'Model'. Other fields are optional.
    """

    grid = expand_table(table)

    version_position = find_column(
        grid,
        VERSION_HEADERS,
    )

    if version_position is None:
        return []

    years_position = find_column(
        grid,
        YEAR_HEADERS,
    )

    engine_position = find_column(
        grid,
        ENGINE_HEADERS,
        allow_prefix=True,
    )

    power_position = find_column(
        grid,
        POWER_HEADERS,
    )

    header_positions = [
        position
        for position in (
            version_position,
            years_position,
            engine_position,
            power_position,
        )
        if position is not None
    ]

    data_start_row = max(
        row_index
        for row_index, _ in header_positions
    ) + 1

    version_column = version_position[1]

    years_column = (
        years_position[1]
        if years_position is not None
        else None
    )

    engine_column = (
        engine_position[1]
        if engine_position is not None
        else None
    )

    power_column = (
        power_position[1]
        if power_position is not None
        else None
    )

    rows: list[VersionRow] = []
    seen: set[VersionRow] = set()

    for row in grid[data_start_row:]:
        version = get_row_value(
            row,
            version_column,
        )

        if version is None:
            continue

        # Guard against accidentally reading another header row.
        if normalize_text(version) in {
            normalize_text(header)
            for header in VERSION_HEADERS
        }:
            continue

        parsed_row = VersionRow(
            version=version,
            years=get_row_value(
                row,
                years_column,
            ),
            engine=get_row_value(
                row,
                engine_column,
            ),
            power=get_row_value(
                row,
                power_column,
            ),
        )

        if parsed_row in seen:
            continue

        seen.add(parsed_row)
        rows.append(parsed_row)

    return rows


def extract_version_rows(
    soup: BeautifulSoup,
) -> list[VersionRow]:
    """
    Parse version records from all relevant Wikipedia tables on a page.
    """

    rows: list[VersionRow] = []
    seen: set[VersionRow] = set()

    for table in soup.select("table.wikitable"):
        table_rows = parse_version_table(table)

        for row in table_rows:
            if row in seen:
                continue

            seen.add(row)
            rows.append(row)

    return rows