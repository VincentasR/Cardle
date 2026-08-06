from cardle.extract.data.fetch import fetch_page
from cardle.extract.data.version import extract_versions


url = "https://en.wikipedia.org/wiki/BMW_6_Series_(E24)"

soup = fetch_page(url)
versions = extract_versions(soup)

for version in versions:
    print(version)