import re
import unicodedata

from .ids import manufacturer_id, slugify


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


def parse_engine_usage(
    value: str,
    manufacturer_name: str,
) -> tuple[
    dict | None,
    dict | None,
    dict | None,
    dict | None,
]:
    """
    Parse a raw engine description into:

        EngineSeries
        EngineFamily
        Engine
        Engine usage

    For BMW:

        "2.0 L B48B20O1 I4"

            EngineSeries:
                B

            EngineFamily:
                B48

            Engine:
                B48B20O1

            Usage:
                displacement_l = 2.0


        "2.0 L B48 I4"

            EngineSeries:
                B

            EngineFamily:
                B48

            Engine:
                None

    If a manufacturer-specific family rule is not available,
    the exact engine code is preserved as an Engine, but no
    EngineSeries or EngineFamily is invented.
    """

    if not value:
        return None, None, None, None

    engine_code = _parse_engine_code(
        value
    )

    if engine_code is None:
        return None, None, None, None

    displacement_l = _parse_displacement(
        value
    )

    (
        cylinder_count,
        arrangement,
    ) = _parse_cylinders(
        value
    )

    (
        series_name,
        family_name,
        specific_engine_code,
    ) = _resolve_engine_hierarchy(
        engine_code=engine_code,
        manufacturer_name=manufacturer_name,
    )

    manufacturer = manufacturer_id(
        manufacturer_name
    )

    # ========================================================
    # EngineSeries
    # ========================================================

    engine_series = None

    if series_name is not None:
        engine_series = {
            "id": slugify(
                f"{manufacturer}_{series_name}"
            ),
            "name": series_name,
            "manufacturer_id": manufacturer,
        }

    # ========================================================
    # EngineFamily
    # ========================================================

    engine_family = None

    if family_name is not None:
        engine_family = {
            "id": slugify(
                f"{manufacturer}_{family_name}"
            ),
            "name": family_name,
            "engine_series_id": (
                engine_series["id"]
                if engine_series is not None
                else None
            ),
        }

    # ========================================================
    # Specific Engine
    # ========================================================

    engine = None

    if specific_engine_code is not None:
        engine = {
            "id": slugify(
                f"{manufacturer}_{specific_engine_code}"
            ),
            "code": specific_engine_code,
            "engine_family_id": (
                engine_family["id"]
                if engine_family is not None
                else None
            ),
        }

    # ========================================================
    # Version -> Engine usage
    # ========================================================

    engine_usage = {
        "engine_series_id": (
            engine_series["id"]
            if engine_series is not None
            else None
        ),
        "engine_family_id": (
            engine_family["id"]
            if engine_family is not None
            else None
        ),
        "engine_id": (
            engine["id"]
            if engine is not None
            else None
        ),
        "displacement_l": displacement_l,
        "cylinder_count": cylinder_count,
        "arrangement": arrangement,
    }

    return (
        engine_series,
        engine_family,
        engine,
        engine_usage,
    )


def _resolve_engine_hierarchy(
    engine_code: str,
    manufacturer_name: str,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    """
    Resolve a manufacturer-specific engine hierarchy.

    Returns:
        (
            engine_series_name,
            engine_family_name,
            specific_engine_code,
        )

    The schema is generic, but engine naming conventions are
    manufacturer-specific.

    If no manufacturer-specific resolver exists, preserve the
    exact engine code without inventing a family.
    """

    manufacturer = (
        manufacturer_name
        .strip()
        .casefold()
    )

    if manufacturer == "bmw":
        return _resolve_bmw_engine_hierarchy(
            engine_code
        )

    # Unknown manufacturer convention.
    # Preserve the exact code, but do not guess a hierarchy.
    return (
        None,
        None,
        engine_code,
    )


def _resolve_bmw_engine_hierarchy(
    engine_code: str,
) -> tuple[
    str | None,
    str,
    str | None,
]:
    """
    Resolve BMW engine codes into three canonical levels.

    Examples:

        B48B20M0
            series  = B
            family  = B48
            engine  = B48B20M0

        B48B20O1
            series  = B
            family  = B48
            engine  = B48B20O1

        B48
            series  = B
            family  = B48
            engine  = None

        N55B30M0
            series  = N
            family  = N55
            engine  = N55B30M0

        M30B35
            series  = M
            family  = M30
            engine  = M30B35

        M52TUB28
            series  = M
            family  = M52
            engine  = M52TUB28

        M88/3
            series  = M
            family  = M88
            engine  = M88/3

    Historical codes that do not clearly follow this structure
    are kept conservatively.

    Example:

        M118
            series  = M
            family  = M118
            engine  = None
    """

    if not engine_code:
        return None, engine_code, None

    series_name = (
        engine_code[0]
        if engine_code[0].isalpha()
        else None
    )

    # Common BMW pattern:
    # one letter + two digits form the family,
    # when followed by end-of-string or another code marker.
    #
    # This avoids reducing codes such as M118 to M11.
    family_match = re.match(
        r"^([A-Z])(\d{2})(?=$|[A-Z/-])",
        engine_code,
    )

    if family_match is not None:
        family_name = (
            family_match.group(1)
            + family_match.group(2)
        )

        if engine_code == family_name:
            specific_engine_code = None
        else:
            specific_engine_code = (
                engine_code
            )

        return (
            series_name,
            family_name,
            specific_engine_code,
        )

    # Conservative historical fallback:
    # keep the supplied code as the family rather than
    # inventing a shorter family.
    return (
        series_name,
        engine_code,
        None,
    )


def _normalize_engine_code(
    value: str,
) -> str:
    """
    Normalize equivalent spellings of an engine code.

    Examples:
        M52TÜB28 -> M52TUB28
        M52TUB28 -> M52TUB28
    """

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    return value.upper()


def _parse_engine_code(
    value: str,
) -> str | None:
    """
    Find the first plausible engine code in a raw engine
    description.

    Cylinder-layout tokens such as V8, V12 and I6 are
    deliberately excluded because they describe architecture
    rather than engine identity.
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

        if CYLINDER_TOKEN_PATTERN.fullmatch(
            token
        ):
            continue

        if ENGINE_CODE_PATTERN.fullmatch(
            token
        ):
            return _normalize_engine_code(
                token
            )

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
    """

    match = re.search(
        r"\bI(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    match = re.search(
        r"\binline[-\s]?(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    match = re.search(
        r"\bstraight[-\s]?(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "Inline"

    match = re.search(
        r"\bV(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "V"

    match = re.search(
        r"\bW(\d{1,2})\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), "W"

    match = re.search(
        r"\b(\d{1,2})[-\s]?cylinder\b",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), None

    return None, None