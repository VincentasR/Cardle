from fetch import fetch_page
from infobox import extract_infobox
from manufacturer import extract_manufacturer


def scrape_car_page(url: str) -> dict:
    """Run the current Cardle Wikipedia extraction pipeline."""

    soup = fetch_page(url)

    infobox = extract_infobox(soup)
    manufacturer = extract_manufacturer(infobox)

    return {
        "manufacturer": manufacturer,
    }


if __name__ == "__main__":
    page_url = (
        "https://en.wikipedia.org/wiki/"
        "BMW_6_Series_(E24)"
    )

    result = scrape_car_page(page_url)

    print(result)