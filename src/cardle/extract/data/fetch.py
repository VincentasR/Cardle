import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "CardleScraper/0.1"
}


def fetch_page(url: str) -> BeautifulSoup:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")
print(fetch_page("https://en.wikipedia.org/wiki/BMW_6_Series_(E24)"))