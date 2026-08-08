import requests

from cardle.extract.data.discover.bmw import (
    discover_bmw_vehicle_pages,
)
from cardle.extract.data.engine import (
    extract_variant_engines,
    extract_version_engines,
)
from cardle.extract.data.fetch import fetch_page
from cardle.extract.data.infobox import extract_infobox
from cardle.extract.data.manufacturer import extract_manufacturer
from cardle.extract.data.model import extract_model
from cardle.extract.data.section import extract_section
from cardle.extract.data.table.version_table import (
    extract_version_rows,
)
from cardle.extract.data.variant import extract_variants
from cardle.extract.data.version import extract_versions
from cardle.extract.data.years import extract_version_years
from cardle.extract.data.production import extract_variant_production
from cardle.extract.data.power import extract_version_power




def scrape_car_page(
    vehicle: dict,
) -> dict:
    """
    Run the Cardle Wikipedia extraction pipeline for one discovered
    vehicle.

    The discovery record is kept as context rather than passing only
    the URL.
    """

    url = vehicle["url"]

    # ---------------------------------------------------------
    # Fetch Wikipedia page
    # ---------------------------------------------------------

    soup = fetch_page(url)

    # ---------------------------------------------------------
    # General page-level extraction
    # ---------------------------------------------------------

    infobox = extract_infobox(soup)

    manufacturer = extract_manufacturer(
        infobox
    )

    # ---------------------------------------------------------
    # Model
    # ---------------------------------------------------------

    model = (
        extract_model(
            soup=soup,
            manufacturer=manufacturer,
            discovery_name=vehicle.get("name"),
        )
        if manufacturer is not None
        else None
    )

    # ---------------------------------------------------------
    # Variant
    #
    # Discovery information is deliberately supplied here.
    # ---------------------------------------------------------

    variants = (
        extract_variants(
            soup=soup,
            manufacturer=manufacturer,
            discovery_name=vehicle.get("name"),
            model=model,
        )
        if manufacturer is not None
        else []
    )
    variant_production = extract_variant_production(
        infobox=infobox,
        variants=variants,
    )
    # ---------------------------------------------------------
    # Scope article to the requested generation/variant
    #
    # Example:
    # BMW X3 article + G01
    # -> only G01 section
    # ---------------------------------------------------------

    section = extract_section(
        soup=soup,
        variant_codes=variants,
    )

    # ---------------------------------------------------------
    # Parse specification tables ONCE
    # ---------------------------------------------------------

    version_rows = extract_version_rows(
        section
    )

    versions = extract_versions(
        version_rows
    )
    version_years = extract_version_years(
        version_rows
    )

    version_power = extract_version_power(
        version_rows
    )
    # ---------------------------------------------------------
    # Engine relationships
    # ---------------------------------------------------------

    if versions:
        version_engines = extract_version_engines(
            version_rows
        )

        variant_engines = []

    else:
        version_engines = []

        variant_engines = extract_variant_engines(
            soup=section,
            infobox=infobox,
            variants=variants,
            versions=versions,
            
        )

    # ---------------------------------------------------------
    # Raw extracted result
    # ---------------------------------------------------------

    return {
        "manufacturer": manufacturer,
        "model": model,
        "variants": variants,
        "versions": versions,
        "version_engines": version_engines,
        "variant_engines": variant_engines,
        "variant_production": variant_production,
        "version_years": version_years,
        "version_power": version_power,
    }


if __name__ == "__main__":
    vehicle_pages = discover_bmw_vehicle_pages()

    results = []

    for vehicle in vehicle_pages:
        url = vehicle["url"]

        print(
            f"Scraping: "
            f"{vehicle['name']} — {url}"
        )

        try:
            # IMPORTANT:
            # Pass the whole discovery record, not only the URL.
            extracted_data = scrape_car_page(
                vehicle
            )

        except requests.HTTPError as error:
            status_code = error.response.status_code

            if status_code == 404:
                print(
                    f"Skipping missing page: {url}"
                )
                continue

            raise

        print(vehicle)
        print(extracted_data)

        results.append(
            {
                **vehicle,
                **extracted_data,
            }
        )