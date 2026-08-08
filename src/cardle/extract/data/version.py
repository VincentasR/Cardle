import re

from cardle.extract.data.table.version_table import VersionRow


INVALID_VERSION_NAMES = {
    "model",
    "model years",
    "year",
    "years",
    "total",
    "totals",
    "powertrain",
    "motor",
    "engine",
    "battery",
    "battery capacity",
    "battery capacity (usable)",
    "range",
    "power",
    "power (peak)",
    "torque",
    "torque (peak)",
    "top speed",
    "weight",
    "kerb weight",
    "gross weight",
    "production starts from",
}


def is_valid_version_name(value: str) -> bool:
    """
    Reject values that are clearly not vehicle versions.

    This is only a final sanity check. Actual table interpretation
    belongs in version_table.py.
    """

    value = " ".join(value.split()).strip()

    if not value:
        return False

    normalized = value.casefold()

    if normalized in INVALID_VERSION_NAMES:
        return False

    # Example: 1963
    if re.fullmatch(r"\d{4}", value):
        return False

    # Examples:
    # 1963–1968
    # 1963-68
    if re.fullmatch(
        r"\d{4}\s*[-–—]\s*\d{2,4}",
        value,
    ):
        return False

    return True


def extract_versions(
    rows: list[VersionRow],
) -> list[str]:
    """
    Extract unique, plausible version names from parsed version rows.
    """

    versions: list[str] = []
    seen: set[str] = set()

    for row in rows:
        if row.version is None:
            continue

        version = " ".join(
            row.version.split()
        ).strip()

        if not is_valid_version_name(version):
            continue

        if version in seen:
            continue

        seen.add(version)
        versions.append(version)

    return versions