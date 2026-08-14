import re
import unicodedata
from .ids import slugify


CYLINDER_TOKEN_PATTERN = re.compile(
    r"^(?:"
    r"I\d{1,2}|"
    r"L\d{1,2}|"
    r"V\d{1,2}|"
    r"W\d{1,2}|"
    r"H\d{1,2}"
    r")$",
    re.IGNORECASE,
)


ENGINE_CODE_PATTERN = re.compile(
    r"^[A-Za-zÄÖÜäöü]"
    r"[A-Za-z0-9ÄÖÜäöü/-]*"
    r"\d"
    r"[A-Za-z0-9ÄÖÜäöü/-]*$"
)

def _normalize_engine_code(
    value: str,
) -> str:
    """
    Normalize equivalent spellings of an engine code.

    Examples:
        M52TÜB28 -> M52TUB28
        M52TUB28 -> M52TUB28

    Engine codes are identifiers, so using a stable ASCII
    representation avoids creating different canonical names
    for the same engine family.
    """

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    return value.upper()

def parse_engine_usage(
    value: str,
) -> tuple[dict | None, dict | None]:
    """
    Parse a raw engine description into:

        EngineFamily
        Engine usage

    Examples:
        "3.0 L N52 inline-6"
            -> N52, 3.0 L

        "4.4 L N62 V8"
            -> N62, 4.4 L

        "M30B28 SOHC I6"
            -> M30B28

        "5.4 L M73TÜB54 V12"
            -> M73TÜB54, 5.4 L

    Cylinder-layout tokens such as V8, V12 and I6 are
    deliberately excluded from engine-code detection.
    """

    if not value:
        return None, None

    engine_code = _parse_engine_code(value)

    if engine_code is None:
        return None, None

    displacement_l = _parse_displacement(value)

    cylinder_count, arrangement = _parse_cylinders(
        value
    )

    engine_family = {
        "id": slugify(engine_code),
        "name": engine_code,
        "cylinder_count": cylinder_count,
        "arrangement": arrangement,
    }

    engine_usage = {
        "engine_family_id": engine_family["id"],
        "displacement_l": displacement_l,
    }

    return engine_family, engine_usage


def _parse_engine_code(
    value: str,
) -> str | None:
    """
    Find the first plausible engine code in a raw engine
    description.

    This deliberately rejects cylinder-layout tokens such as:

        I4
        I6
        V8
        V10
        V12
        W12

    because those describe engine architecture rather than
    engine identity.
    """

    tokens = re.split(
        r"\s+",
        value.strip(),
    )

    for token in tokens:
        token = token.strip(
            "(),[];"
        )

        if not token:
            continue

        # Do not interpret V8/V12/I6/etc. as engine codes.
        if CYLINDER_TOKEN_PATTERN.fullmatch(token):
            continue

        if ENGINE_CODE_PATTERN.fullmatch(token):
            return _normalize_engine_code(token)

    return None


def _parse_displacement(
    value: str,
) -> float | None:
    """
    Extract displacement expressed in litres.

    Example:
        "4.4 L N62 V8"
            -> 4.4
    """

    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*[Ll]\b",
        value,
    )

    if match is None:
        return None

    return float(
        match.group(1)
    )


def _parse_cylinders(
    value: str,
) -> tuple[int | None, str | None]:
    """
    Extract cylinder count and canonical arrangement.

    Examples:
        I6          -> 6, Inline
        inline-6    -> 6, Inline
        straight-6  -> 6, Inline
        6-cylinder  -> 6, None
        V8          -> 8, V
        V12         -> 12, V
    """

    # I6 / I4 etc.
    match = re.search(
        r"\bI(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    # inline-6 / inline 6
    match = re.search(
        r"\binline[-\s]?(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    # straight-6 / straight 6
    match = re.search(
        r"\bstraight[-\s]?(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    # V8 / V10 / V12
    match = re.search(
        r"\bV(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "V"

    # W12 etc.
    match = re.search(
        r"\bW(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "W"

    # Generic "4-cylinder", where arrangement isn't stated.
    match = re.search(
        r"\b(\d{1,2})[-\s]?cylinder\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), None

    return None, None