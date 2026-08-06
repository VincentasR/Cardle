import requests

from cardle.extract.data.fetch import fetch_page
from cardle.extract.data.infobox import extract_infobox
from cardle.extract.data.manufacturer import extract_manufacturer
from cardle.extract.data.model import extract_model
from cardle.extract.data.discover.bmw import discover_bmw_vehicle_pages
from cardle.extract.data.variant import extract_variants
from cardle.extract.data.version import extract_versions
from cardle.extract.data.engine import (
    extract_variant_engines,
    extract_version_engines,
)
from cardle.extract.data.table.version_table import extract_version_rows
from cardle.extract.data.section import extract_section


def scrape_car_page(url: dict) -> dict:
    soup = fetch_page(url)

    infobox = extract_infobox(soup)
    manufacturer = extract_manufacturer(infobox)

    model = (
        extract_model(soup, manufacturer)
        if manufacturer is not None
        else None
    )

    variants = extract_variants(
        soup=soup,
        manufacturer=manufacturer,
        discovery_name=vehicle.get("name"),
        model=model,
    )
    section = extract_section(
    soup=soup,
    variant_codes=variants,
    )
    section = extract_section(
    soup=soup,
    variant_codes=variants,
    )   

   
    version_rows = extract_version_rows(section)

    versions = extract_versions(version_rows)

    if versions:
        version_engines = extract_version_engines(version_rows)
        variant_engines = []
    else:
        version_engines = []
        variant_engines = extract_variant_engines(
            section,
            infobox,
            variants,
            versions,
        )
    return {
        "manufacturer": manufacturer,
        "model": model,
        "variants": variants,
        "versions": versions,
        "version_engines": version_engines,
        "variant_engines": variant_engines,
    }

if __name__ == "__main__":
    vehicle_pages = discover_bmw_vehicle_pages()
    results = []
    vehicle_pages = ({"url":"https://en.wikipedia.org/wiki/Volkswagen_Golf_Mk2"},)
    for vehicle in vehicle_pages:
        url = vehicle["url"]
        # print(vehicle)
        # print(f"Scraping: {vehicle['name']} — {url}")

        try:
            extracted_data = scrape_car_page(url)

        except requests.HTTPError as error:
            status_code = error.response.status_code

            if status_code == 404:
                print(f"Skipping missing page: {url}")
                continue

            raise
        print(vehicle)
        results.append(
            {
                **extracted_data,
            }
        )
        print(extracted_data)
        
    
    