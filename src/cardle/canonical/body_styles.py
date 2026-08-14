import re


# ============================================================
# Generic body-style vocabulary
#
# These are normal descriptive body-style terms that can be
# used directly when they appear in the source.
# ============================================================

BODY_STYLE_ALIASES = {
    "coupe": "Coupe",
    "coupé": "Coupe",

    "sedan": "Sedan",
    "saloon": "Sedan",

    "wagon": "Wagon",
    "estate": "Wagon",
    "touring": "Wagon",
    "station wagon": "Wagon",

    "hatchback": "Hatchback",

    "fastback": "Fastback",
    "liftback": "Fastback",

    "convertible": "Convertible",
    "cabriolet": "Convertible",

    "roadster": "Roadster",

    "suv": "SUV",
    "sport utility vehicle": "SUV",

    "pickup": "Pickup",
    "pick-up": "Pickup",
}


# ============================================================
# Marketing/body-style labels
#
# These are only used as a FALLBACK if the source does not
# already contain a normal generic body-style term.
#
# This prevents:
#
#     "5-door liftback (Gran Coupé)"
#
# from becoming both:
#
#     Fastback
#     Sedan
#
# The explicit "liftback" is stronger evidence.
# ============================================================

MARKETING_BODY_STYLE_ALIASES = {
    "gran coupé": "Sedan",
    "gran coupe": "Sedan",

    "gran turismo": "Fastback",
}


def parse_body_styles(
    value: str,
) -> list[str]:
    """
    Normalize raw Wikipedia body-style text into Cardle's
    canonical body-style vocabulary.

    Examples:

        "2-door coupé"
            -> ["Coupe"]

        "4-door saloon"
            -> ["Sedan"]

        "5-door estate"
            -> ["Wagon"]

        "5-door fastback"
            -> ["Fastback"]

        "5-door liftback"
            -> ["Fastback"]

        "Gran Coupé"
            -> ["Sedan"]

        "5-door liftback (Gran Coupé)"
            -> ["Fastback"]

    Explicit generic body-style wording always takes priority
    over marketing labels.
    """

    if not value:
        return []

    value_lower = value.casefold()

    # --------------------------------------------------------
    # Remove marketing labels before looking for generic
    # styles.
    #
    # Otherwise:
    #
    #     "Gran Coupé"
    #
    # would accidentally match:
    #
    #     "coupé" -> Coupe
    # --------------------------------------------------------

    generic_text = value_lower

    for marketing_alias in (
        MARKETING_BODY_STYLE_ALIASES
    ):
        generic_text = re.sub(
            _phrase_pattern(
                marketing_alias
            ),
            " ",
            generic_text,
            flags=re.IGNORECASE,
        )

    # --------------------------------------------------------
    # First try explicit generic body-style terms.
    # --------------------------------------------------------

    found = _find_body_styles(
        generic_text,
        BODY_STYLE_ALIASES,
    )

    if found:
        return found

    # --------------------------------------------------------
    # No explicit generic body style was found.
    #
    # Fall back to recognized marketing terminology.
    # --------------------------------------------------------

    return _find_body_styles(
        value_lower,
        MARKETING_BODY_STYLE_ALIASES,
    )


def _find_body_styles(
    value: str,
    aliases: dict[str, str],
) -> list[str]:
    """
    Find all canonical body styles represented in a piece of
    source text while preserving deterministic order.
    """

    found = []

    # Longer aliases first.
    #
    # Example:
    #
    #     "station wagon"
    #
    # should be considered before:
    #
    #     "wagon"
    #
    for alias in sorted(
        aliases,
        key=len,
        reverse=True,
    ):
        canonical = aliases[
            alias
        ]

        if not re.search(
            _phrase_pattern(alias),
            value,
            flags=re.IGNORECASE,
        ):
            continue

        if canonical not in found:
            found.append(
                canonical
            )

    return found


def _phrase_pattern(
    phrase: str,
) -> str:
    """
    Create a boundary-aware regex for a phrase.

    Spaces inside aliases are allowed to match arbitrary
    whitespace.
    """

    parts = [
        re.escape(part)
        for part in phrase.split()
    ]

    body = r"\s+".join(
        parts
    )

    return (
        r"(?<![A-Za-z0-9])"
        + body
        + r"(?![A-Za-z0-9])"
    )