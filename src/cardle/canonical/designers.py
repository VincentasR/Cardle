import re


# ============================================================
# Patterns
# ============================================================

REFERENCE_PATTERN = re.compile(
    r"\s*\[\s*[^\]]+\s*\]\s*"
)

PARENTHETICAL_PATTERN = re.compile(
    r"\s*\([^()]*\)\s*"
)

ROLE_PREFIX_PATTERN = re.compile(
    r"^(?:"
    r"designer|designers|"
    r"engineer|engineers|"
    r"stylist|stylists|"
    r"chief designer|"
    r"design director|"
    r"exterior designer|"
    r"interior designer"
    r")"
    r"\s*:\s*",
    flags=re.IGNORECASE,
)


# ============================================================
# Obvious non-person values
#
# We keep this deliberately conservative.
# We are NOT trying to determine whether arbitrary text is a
# human name.
# ============================================================

NON_PERSON_EXACT_VALUES = {
    "none",
    "unknown",
    "n/a",
    "na",
}

NON_PERSON_MARKERS = {
    "design team",
    "design studio",
    "design department",
    "designworks",
}


def parse_designers(
    value: str,
) -> list[str]:
    """
    Convert one raw Wikipedia Designer entry into canonical
    human designer names.

    Examples:

        "Ted Lee (exterior)"
            -> ["Ted Lee"]

        "Harm Lagaay (1986)"
            -> ["Harm Lagaay"]

        "Michael de Bono (F31, 2009)"
            -> ["Michael de Bono"]

        "Engineers: Fritz Fiedler"
            -> ["Fritz Fiedler"]

        "Giorgetto Giugiaro at Bertone"
            -> ["Giorgetto Giugiaro"]

        "Ercole Spada and J Mays under Claus Luthe"
            -> [
                "Ercole Spada",
                "J Mays",
            ]

    Important:
    "under Claus Luthe" is treated as supervisory/contextual
    information rather than another direct designer.

    We do not invent or expand names:

        "J Mays"

    remains:

        "J Mays"

    rather than guessing a fuller name.
    """

    if not value:
        return []

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # Remove Wikipedia references.
    # --------------------------------------------------------

    value = REFERENCE_PATTERN.sub(
        " ",
        value,
    )

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # Remove parenthetical metadata.
    #
    # Examples:
    #
    #     Ted Lee (exterior)
    #     Harm Lagaay (1986)
    #     Michael de Bono (F31, 2009)
    #     Joji Nagashima (saloon and estate)
    #
    # Variant/body association has ALREADY happened in the raw
    # scraper, so this information is no longer required for
    # canonical identity.
    #
    # Repeat so nested/simple multiple groups are handled.
    # --------------------------------------------------------

    while PARENTHETICAL_PATTERN.search(
        value
    ):
        value = PARENTHETICAL_PATTERN.sub(
            " ",
            value,
        )

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # "under X" is contextual/supervisory information.
    #
    # Example:
    #
    #     Ercole Spada and J Mays under Claus Luthe
    #
    # Direct designers:
    #
    #     Ercole Spada
    #     J Mays
    #
    # We do NOT create an additional DESIGNED_BY relationship
    # for Claus Luthe from this phrase.
    # --------------------------------------------------------

    value = re.split(
        r"\s+\bunder\b\s+",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # --------------------------------------------------------
    # Explicit "and" is now safe enough to use because the raw
    # scraper already preserved individual HTML designer items.
    #
    # This is therefore mainly for genuine textual constructs
    # such as:
    #
    #     Ercole Spada and J Mays
    # --------------------------------------------------------

    parts = re.split(
        r"\s+\band\b\s+",
        value,
        flags=re.IGNORECASE,
    )

    result = []

    for part in parts:
        designer = clean_designer_name(
            part
        )

        if not designer:
            continue

        if _is_obvious_non_person(
            designer
        ):
            continue

        if designer not in result:
            result.append(
                designer
            )

    return result


def clean_designer_name(
    value: str,
) -> str | None:
    """
    Clean one individual designer value.

    Removes:

        - role prefixes
        - Wikipedia references
        - parenthetical metadata
        - company/studio affiliation introduced with "at"

    while preserving the person's actual source spelling.
    """

    if not value:
        return None

    value = _normalize_whitespace(
        value
    )

    value = REFERENCE_PATTERN.sub(
        " ",
        value,
    )

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # Remove prefixes such as:
    #
    #     Engineers: Fritz Fiedler
    #     Stylist: Peter Szymanowski
    # --------------------------------------------------------

    value = ROLE_PREFIX_PATTERN.sub(
        "",
        value,
    )

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # Remove remaining parenthetical annotations.
    # --------------------------------------------------------

    while PARENTHETICAL_PATTERN.search(
        value
    ):
        value = PARENTHETICAL_PATTERN.sub(
            " ",
            value,
        )

    value = _normalize_whitespace(
        value
    )

    # --------------------------------------------------------
    # Remove affiliation.
    #
    # Examples:
    #
    #     Giorgetto Giugiaro at Bertone
    #         -> Giorgetto Giugiaro
    #
    #     Giorgetto Giugiaro at Italdesign
    #         -> Giorgetto Giugiaro
    #
    # The organisation may be useful later as provenance or a
    # design-studio relationship, but it must not be part of
    # Designer identity.
    # --------------------------------------------------------

    value = re.sub(
        r"\s+\bat\b\s+.+$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = _normalize_whitespace(
        value
    )

    value = value.strip(
        " ,;:-–—"
    )

    if not value:
        return None

    return value


def _is_obvious_non_person(
    value: str,
) -> bool:
    """
    Reject values that clearly are not human designers.

    This intentionally does NOT try to implement a generic
    human-name detector.
    """

    normalized = (
        value.casefold()
        .strip()
    )

    if normalized in NON_PERSON_EXACT_VALUES:
        return True

    # --------------------------------------------------------
    # BMW example:
    #
    #     Vision EfficientDynamics
    #
    # This is a concept/program name, not a person.
    #
    # "Vision ..." is sufficiently structural to reject here
    # without adding BMW-specific names.
    # --------------------------------------------------------

    if normalized.startswith(
        "vision "
    ):
        return True

    for marker in NON_PERSON_MARKERS:
        if marker in normalized:
            return True

    return False


def _normalize_whitespace(
    value: str,
) -> str:
    return " ".join(
        value.split()
    )