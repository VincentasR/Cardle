from __future__ import annotations

import re

from bs4 import Tag


def normalize_text(text: str) -> str:
    """
    Normalize text for comparisons.

    Example:
        "  Model   Code " -> "model code"
    """

    return " ".join(text.casefold().split())


def clean_value(value: str) -> str:
    """
    Remove common Wikipedia citation markers and normalize whitespace.

    Examples:
        "184 PS [ 12 ]" -> "184 PS"
        "BMW\\n635CSi"   -> "BMW 635CSi"
    """

    value = re.sub(r"\[\s*\d+\s*\]", "", value)

    return " ".join(value.split())


def parse_span(cell: Tag, attribute: str) -> int:
    """
    Safely parse rowspan or colspan.

    Invalid or missing values are treated as 1.
    """

    raw_value = cell.get(attribute, 1)

    try:
        span = int(raw_value)
    except (TypeError, ValueError):
        return 1

    return max(span, 1)


def expand_table(table: Tag) -> list[list[Tag | None]]:
    """
    Expand an HTML table into a rectangular grid.

    HTML tables may omit cells because of rowspan and colspan. This
    function repeats references to spanning cells so every logical
    column retains the same index across rows.

    The returned cells are still BeautifulSoup Tag objects.
    """

    grid: list[list[Tag | None]] = []

    # Maps a logical column index to:
    #     (cell, number of later rows still occupied)
    active_rowspans: dict[int, tuple[Tag, int]] = {}

    for html_row in table.find_all("tr"):
        row: list[Tag | None] = []

        cells = html_row.find_all(
            ["th", "td"],
            recursive=False,
        )

        column_index = 0
        cell_index = 0

        while cell_index < len(cells) or active_rowspans:
            if column_index in active_rowspans:
                cell, remaining_rows = active_rowspans[column_index]

                row.append(cell)

                if remaining_rows <= 1:
                    del active_rowspans[column_index]
                else:
                    active_rowspans[column_index] = (
                        cell,
                        remaining_rows - 1,
                    )

                column_index += 1
                continue

            if cell_index >= len(cells):
                # There may still be active rowspans at larger column
                # indices, so advance until one is reached.
                later_columns = [
                    index
                    for index in active_rowspans
                    if index > column_index
                ]

                if not later_columns:
                    break

                next_column = min(later_columns)

                row.extend(
                    [None] * (next_column - column_index)
                )
                column_index = next_column
                continue

            cell = cells[cell_index]
            cell_index += 1

            rowspan = parse_span(cell, "rowspan")
            colspan = parse_span(cell, "colspan")

            for offset in range(colspan):
                row.append(cell)

                if rowspan > 1:
                    active_rowspans[column_index + offset] = (
                        cell,
                        rowspan - 1,
                    )

            column_index += colspan

        grid.append(row)

    maximum_width = max(
        (len(row) for row in grid),
        default=0,
    )

    for row in grid:
        row.extend(
            [None] * (maximum_width - len(row))
        )

    return grid


def get_cell_text(cell: Tag | None) -> str | None:
    """
    Return cleaned visible text from a cell.
    """

    if cell is None:
        return None

    value = clean_value(
        cell.get_text(" ", strip=True)
    )

    return value or None


def find_header_position(
    grid: list[list[Tag | None]],
    column_name: str,
) -> tuple[int, int] | None:
    """
    Find a header cell and return:

        (row_index, column_index)

    Only th elements are considered headers.
    """

    requested_name = normalize_text(column_name)

    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell is None or cell.name != "th":
                continue

            value = get_cell_text(cell)

            if value is None:
                continue

            if normalize_text(value) == requested_name:
                return row_index, column_index

    return None


def find_first_header_position(
    grid: list[list[Tag | None]],
    column_names: set[str],
) -> tuple[int, int] | None:
    """
    Find the first header matching any supported name.

    Example:
        {"engine", "engine code"}
    """

    normalized_names = {
        normalize_text(name)
        for name in column_names
    }

    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell is None or cell.name != "th":
                continue

            value = get_cell_text(cell)

            if value is None:
                continue

            if normalize_text(value) in normalized_names:
                return row_index, column_index

    return None


def is_section_heading(cell: Tag | None) -> bool:
    """
    Detect table-wide or multi-column section headings.

    Examples:
        "US market specifications"
        "Petrol engines"
    """

    if cell is None:
        return False

    return parse_span(cell, "colspan") > 1