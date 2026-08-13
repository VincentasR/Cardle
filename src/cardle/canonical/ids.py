import re
import unicodedata


def slugify(value: str) -> str:
    """Convert a human-readable value into an ID-safe string."""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)

    return value.strip("_")


def manufacturer_id(name: str) -> str:
    return slugify(name)


def model_id(manufacturer: str, model: str) -> str:
    return f"{manufacturer_id(manufacturer)}_{slugify(model)}"


def variant_id(manufacturer: str, model: str, variant: str) -> str:
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