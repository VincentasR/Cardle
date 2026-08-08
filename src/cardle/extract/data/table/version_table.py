from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from cardle.extract.data.table.parser import (
    expand_table,
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


# These are specification/summary labels that Wikipedia may place
# vertically in the first column of a transposed table.
INVALID_VERSION_LABELS = {
    "model",
    "model year",
    "model years",
    "year",
    "years",
    "total",
    "totals",
    "powertrain",
    "engine",
    "engine code",
    "motor",
    "motors",
    "battery",
    "battery capacity",
    "battery capacity usable",
    "battery capacity (usable)",
    "range",
    "power",
    "power peak",
    "power (peak)",
    "torque",
    "torque peak",
    "torque (peak)",
    "top speed",
    "weight",
    "weight eu",
    "weight (eu)",
    "kerb weight",
    "curb weight",
    "gross weight",
    "production starts from",
    "production start",
    "production",
}


INVALID_VERSION_PREFIXES = {
    "range ",
    "range (",
    "electric power consumption",
    "acceleration ",
    "acceleration 0",
    "dc fast charge",
    "ac on-board charge",
    "battery capacity",
    "production starts",
}


@dataclass(frozen=True)
class VersionRow:
    """
    One logical row extracted from a Wikipedia version/specification table.

    Values are still raw-ish Wikipedia values. Canonicalization happens
    later.
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
    Find the first logical column whose header matches one of the
    supported names.

    With allow_prefix=True:
        "Engine-turbo"
    can match:
        "Engine"
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


def is_valid_version_name(value: str) -> bool:
    """
    Reject values that are clearly not vehicle versions.

    This intentionally stays fairly conservative:
    unusual real version names are allowed, while obvious table labels,
    years and totals are rejected.
    """

    value = " ".join(value.split()).strip()

    if not value:
        return False

    normalized = normalize_text(value).rstrip(":").strip()

    if normalized in INVALID_VERSION_LABELS:
        return False

    if any(
        normalized.startswith(prefix)
        for prefix in INVALID_VERSION_PREFIXES
    ):
        return False

    # Pure calendar year:
    # 1968
    if re.fullmatch(r"\d{4}", value):
        return False

    # Pure year ranges:
    # 1968–1975
    # 1968-75
    # 1968−1975
    if re.fullmatch(
        r"\d{4}\s*[-–—−]\s*\d{2,4}",
        value,
    ):
        return False

    return True


def parse_version_table(
    table: Tag,
) -> list[VersionRow]:
    """
    Parse one Wikipedia table containing vehicle-version information.

    The table must contain a version-like column such as Model or Version.
    Rows that are clearly attributes from transposed specification tables
    are discarded.
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

        # Main sanity check.
        if not is_valid_version_name(version):
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

def normalize_label(value: str) -> str:
    value = normalize_text(value)
    return value.rstrip(":").strip()