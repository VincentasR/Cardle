from bs4 import BeautifulSoup


def normalize_text(text: str) -> str:
    """Collapse repeated whitespace into single spaces."""

    return " ".join(text.split())


def extract_infobox(soup: BeautifulSoup) -> dict[str, str]:
    """
    Extract the first Wikipedia infobox as label-value pairs.

    Example:
    {
        "Manufacturer": "BMW",
        "Production": "1976–1989",
        "Class": "Grand tourer"
    }
    """

    infobox = soup.select_one("table.infobox")

    if infobox is None:
        return {}

    fields: dict[str, str] = {}

    for row in infobox.select("tr"):
        label_cell = row.find("th")
        value_cell = row.find("td")

        if label_cell is None or value_cell is None:
            continue

        label = normalize_text(
            label_cell.get_text(" ", strip=True)
        )

        value = normalize_text(
            value_cell.get_text(" ", strip=True)
        )

        if label:
            fields[label] = value

    return fields