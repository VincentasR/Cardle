import re

from .ids import slugify


def parse_engine_usage(value: str) -> tuple[dict | None, dict | None]:
    """
    Parse a raw Wikipedia engine string into:

    1. a canonical EngineFamily
    2. version-specific engine usage data

    Examples:
        "M30B28 SOHC I6"
        ->
        family:
            {
                "id": "m30b28",
                "name": "M30B28",
                "cylinder_count": 6,
                "arrangement": "Inline"
            }

        usage:
            {
                "engine_family_id": "m30b28",
                "displacement_l": None
            }

        "4.4 L N62 V8"
        ->
        family:
            {
                "id": "n62",
                "name": "N62",
                "cylinder_count": 8,
                "arrangement": "V"
            }

        usage:
            {
                "engine_family_id": "n62",
                "displacement_l": 4.4
            }
    """
    value = value.strip()

    engine_code = _parse_engine_code(value)

    if engine_code is None:
        return None, None

    displacement = _parse_displacement(value)
    cylinder_count, arrangement = _parse_cylinders(value)

    family = {
        "id": slugify(engine_code),
        "name": engine_code,
        "cylinder_count": cylinder_count,
        "arrangement": arrangement,
    }

    usage = {
        "engine_family_id": family["id"],
        "displacement_l": displacement,
    }

    return family, usage


def _parse_engine_code(value: str) -> str | None:
    patterns = [
        # Detailed codes:
        # M30B28, B48B20M0, N52B30
        r"\b[A-Z]\d{2}[A-Z]\d{2}[A-Z0-9]*\b",

        # Codes such as M88/3
        r"\b[A-Z]\d{2}/\d+\b",

        # Family-level codes:
        # N52, N62, S85, M57
        r"\b[A-Z]\d{2}\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            value,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(0).upper()

    return None


def _parse_displacement(value: str) -> float | None:
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*L\b",
        value,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return float(match.group(1))


def _parse_cylinders(
    value: str,
) -> tuple[int | None, str | None]:
    value_lower = value.lower()
    value_upper = value.upper()

    # I6, I4, etc.
    match = re.search(
        r"\bI(\d+)\b",
        value_upper,
    )

    if match:
        return int(match.group(1)), "Inline"

    # inline-6 / inline 6
    match = re.search(
        r"\binline[-\s]?(\d+)\b",
        value_lower,
    )

    if match:
        return int(match.group(1)), "Inline"

    # V8 / V10 / V12
    match = re.search(
        r"\bV(\d+)\b",
        value_upper,
    )

    if match:
        return int(match.group(1)), "V"

    return None, None