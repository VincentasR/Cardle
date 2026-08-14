import re
import unicodedata


SPECIAL_TRANSLITERATIONS = str.maketrans(
    {
        "ø": "o",
        "Ø": "O",
        "đ": "d",
        "Đ": "D",
        "ł": "l",
        "Ł": "L",
        "æ": "ae",
        "Æ": "AE",
        "œ": "oe",
        "Œ": "OE",
        "ß": "ss",
        "ð": "d",
        "Ð": "D",
        "þ": "th",
        "Þ": "Th",
    }
)


def slugify(value: str) -> str:
    """
    Convert a display name into a stable ASCII identifier.

    Examples:
        "BMW"                  -> "bmw"
        "6 Series"             -> "6_series"
        "M635CSi"              -> "m635csi"
        "Anders Thøgersen"     -> "anders_thogersen"
        "Domagoj Đukec"        -> "domagoj_dukec"
        "2 Series Gran Coupé"  -> "2_series_gran_coupe"
    """

    if not value:
        return ""

    # Handle special Latin characters that Unicode
    # decomposition does not reliably convert.
    value = value.translate(
        SPECIAL_TRANSLITERATIONS
    )

    # Decompose accented characters.
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    # Remove combining marks.
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.lower()

    # Replace non-alphanumeric groups with underscores.
    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def manufacturer_id(
    name: str,
) -> str:
    return slugify(
        name
    )


def model_id(
    manufacturer: str,
    model: str,
) -> str:
    return (
        f"{manufacturer_id(manufacturer)}_"
        f"{slugify(model)}"
    )


def variant_id(
    manufacturer: str,
    model: str,
    variant: str,
) -> str:
    return (
        f"{manufacturer_id(manufacturer)}_"
        f"{slugify(model)}_"
        f"{slugify(variant)}"
    )


def version_id(
    manufacturer: str,
    model: str,
    variant: str,
    version: str,
) -> str:
    return (
        f"{manufacturer_id(manufacturer)}_"
        f"{slugify(model)}_"
        f"{slugify(variant)}_"
        f"{slugify(version)}"
    )