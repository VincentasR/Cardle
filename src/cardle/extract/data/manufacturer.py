MANUFACTURER_FIELD_NAMES = {
    "manufacturer",
    "manufacturers",
    "maker",
}


def normalize_field_name(field_name: str) -> str:
    """Normalize an infobox field name for matching."""

    return " ".join(field_name.lower().split())


def extract_manufacturer(
    infobox: dict[str, str],
) -> str | None:
    """Extract the manufacturer value from parsed infobox data."""

    for field_name, value in infobox.items():
        normalized_name = normalize_field_name(field_name)

        if normalized_name in MANUFACTURER_FIELD_NAMES:
            return value

    return None