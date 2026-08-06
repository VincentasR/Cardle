from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from cardle.extract.data.fetch import fetch_page


BMW_LIST_URL = "https://en.wikipedia.org/wiki/List_of_BMW_vehicles"
WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"


def normalize_text(text: str) -> str:
    """Normalize visible HTML text for matching."""
    return " ".join(text.casefold().split())


def expand_table(table: Tag) -> list[list[Tag | None]]:
    """
    Expand an HTML table into a rectangular grid.

    This handles rowspan and colspan so that each logical column keeps
    the same index across rows.
    """

    grid: list[list[Tag | None]] = []
    active_rowspans: dict[int, tuple[Tag, int]] = {}

    for html_row in table.find_all("tr"):
        row: list[Tag | None] = []
        column_index = 0

        cells = html_row.find_all(
            ["th", "td"],
            recursive=False,
        )
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
                break

            cell = cells[cell_index]
            cell_index += 1

            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))

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
        row.extend([None] * (maximum_width - len(row)))

    return grid


def get_header_rows(
    grid: list[list[Tag | None]],
) -> list[list[Tag | None]]:
    """
    Return the initial rows that form the table header.
    """

    header_rows: list[list[Tag | None]] = []

    for row in grid:
        real_cells = [
            cell
            for cell in row
            if cell is not None
        ]

        if not real_cells:
            continue

        if any(cell.name == "td" for cell in real_cells):
            break

        header_rows.append(row)

    return header_rows


def get_column_names(
    header_rows: list[list[Tag | None]],
) -> list[str]:
    """
    Build the full logical name of every table column.
    """

    if not header_rows:
        return []

    column_count = max(len(row) for row in header_rows)
    column_names: list[str] = []

    for column_index in range(column_count):
        parts: list[str] = []

        for row in header_rows:
            if column_index >= len(row):
                continue

            cell = row[column_index]

            if cell is None:
                continue

            text = cell.get_text(" ", strip=True)

            if text and text not in parts:
                parts.append(text)

        column_names.append(" | ".join(parts))

    return column_names


def find_column_index(
    column_names: list[str],
    requested_name: str,
) -> int | None:
    """
    Find a logical column by one of its header levels.

    This matches both:
        Model code

    and:
        Current generation | Model code
    """

    requested = normalize_text(requested_name)

    for index, full_name in enumerate(column_names):
        parts = [
            normalize_text(part)
            for part in full_name.split("|")
        ]

        if requested in parts:
            return index

    return None


def extract_links_from_column(
    table: Tag,
    column_name: str,
) -> list[dict[str, str]]:
    """
    Extract unique Wikipedia links from a named table column.
    """

    grid = expand_table(table)
    header_rows = get_header_rows(grid)
    column_names = get_column_names(header_rows)

    column_index = find_column_index(
        column_names,
        column_name,
    )

    if column_index is None:
        return []

    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    data_rows = grid[len(header_rows):]

    for row in data_rows:
        if column_index >= len(row):
            continue

        cell = row[column_index]

        if cell is None:
            continue

        if cell.name not in {"td", "th"}:
            continue

        # Skip category rows such as "Crossovers/SUVs".
        if int(cell.get("colspan", 1)) > 1:
            continue

        for link in cell.find_all("a", href=True):
            name = link.get_text(" ", strip=True)
            href = link["href"]

            if not name:
                continue

            url = urljoin(
                WIKIPEDIA_BASE_URL,
                href,
            )

            if not url.startswith(
                "https://en.wikipedia.org/wiki/"
            ):
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            results.append(
                {
                    "name": name,
                    "url": url,
                }
            )

    return results


def find_table_with_column(
    soup: BeautifulSoup,
    column_name: str,
) -> Tag | None:
    """
    Find the first BMW wikitable containing a requested column.
    """

    for table in soup.select("table.wikitable"):
        grid = expand_table(table)
        header_rows = get_header_rows(grid)
        column_names = get_column_names(header_rows)

        if find_column_index(column_names, column_name) is not None:
            return table

    return None


def add_vehicle_metadata(
    vehicles: list[dict[str, str]],
    status: str,
) -> list[dict[str, str]]:
    """Add BMW and production status to discovered links."""

    return [
        {
            "manufacturer": "BMW",
            "name": vehicle["name"],
            "status": status,
            "url": vehicle["url"],
        }
        for vehicle in vehicles
    ]


def discover_current_bmw_vehicles(
    soup: BeautifulSoup,
) -> list[dict[str, str]]:
    """
    Current BMW pages are linked under the Model code column.
    """

    table = find_table_with_column(
        soup,
        "Model code",
    )

    if table is None:
        return []

    links = extract_links_from_column(
        table,
        "Model code",
    )

    return add_vehicle_metadata(
        links,
        status="current",
    )


def discover_discontinued_bmw_vehicles(
    soup: BeautifulSoup,
) -> list[dict[str, str]]:
    """
    Old BMW pages are linked under the Model series column.
    """

    table = find_table_with_column(
        soup,
        "Model series",
    )

    if table is None:
        return []

    links = extract_links_from_column(
        table,
        "Model series",
    )

    return add_vehicle_metadata(
        links,
        status="discontinued",
    )


def discover_bmw_vehicle_pages() -> list[dict[str, str]]:
    """Discover all current and discontinued BMW vehicle pages."""

    soup = fetch_page(BMW_LIST_URL)

    current = discover_current_bmw_vehicles(soup)
    discontinued = discover_discontinued_bmw_vehicles(soup)

    return current + discontinued


if __name__ == "__main__":
    vehicles = discover_bmw_vehicle_pages()

    for vehicle in vehicles:
        print(vehicle)

    print()
    print(
        "Current:",
        sum(
            vehicle["status"] == "current"
            for vehicle in vehicles
        ),
    )
    print(
        "Discontinued:",
        sum(
            vehicle["status"] == "discontinued"
            for vehicle in vehicles
        ),
    )
    print("Total:", len(vehicles))
    print(vehicles[0].keys())