import re

from bs4 import BeautifulSoup


# ============================================================
# Date / production-period recognition
# ============================================================

MONTH_PATTERN = (
    r"(?:"
    r"January|February|March|April|May|June|"
    r"July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    r")"
)

YEAR_PATTERN = r"\d{4}"

DATE_PATTERN = (
    rf"(?:"
    rf"{MONTH_PATTERN}"
    rf"\s+"
    rf"(?:\d{{1,2}},?\s+)?"
    rf"{YEAR_PATTERN}"
    rf"|"
    rf"{YEAR_PATTERN}"
    rf")"
)

REFERENCE_PATTERN = (
    r"(?:"
    r"\s*"
    r"\[\s*[^\]]+\s*\]"
    r"\s*"
    r")*"
)

END_DATE_PATTERN = (
    rf"(?:"
    rf"{DATE_PATTERN}"
    rf"|present"
    rf"|current"
    rf"|ongoing"
    rf")"
)

PRODUCTION_PERIOD_PATTERN = re.compile(
    rf"(?P<period>"
    rf"{DATE_PATTERN}"
    rf"{REFERENCE_PATTERN}"
    rf"\s*"
    rf"(?:[–—−-]|\bto\b)"
    rf"\s*"
    rf"{REFERENCE_PATTERN}"
    rf"{END_DATE_PATTERN}"
    rf"{REFERENCE_PATTERN}"
    rf")"
    rf"\s*"
    rf"(?:"
    rf"\("
    rf"(?P<qualifier>[^()]*)"
    rf"\)"
    rf")?",
    flags=re.IGNORECASE,
)


# ============================================================
# Body-style vocabulary
#
# This is ONLY used for matching source qualifiers.
#
# It is not the canonical Cardle body-style vocabulary.
# ============================================================

BODY_STYLE_GROUPS = {
    "sedan": {
        "sedan",
        "saloon",
    },
    "wagon": {
        "wagon",
        "estate",
        "touring",
        "station wagon",
    },
    "coupe": {
        "coupe",
        "coupé",
    },
    "convertible": {
        "convertible",
        "cabriolet",
    },
    "hatchback": {
        "hatchback",
    },
    "fastback": {
        "fastback",
        "liftback",
    },
    "roadster": {
        "roadster",
    },
    "suv": {
        "suv",
        "sport utility",
    },
    "pickup": {
        "pickup",
        "pick-up",
    },
    "lwb": {
        "lwb",
        "long-wheelbase",
        "long wheelbase",
        "extended wheelbase",
    },
}


def extract_variant_production(
    soup: BeautifulSoup,
    infobox: dict[str, str],
    variants: list[str],
    variant_body_styles: list[dict] | None = None,
) -> list[dict]:
    """
    Extract production information for canonical Variants.

    Important safety rule
    ---------------------

    A Wikipedia page can describe an entire model lineage rather
    than one particular generation.

    Example:

        Page title:
            BMW X3

        Infobox:
            Production: 2003–present

        Current scrape target:
            G01

    The production value belongs to the MODEL LINEAGE, not G01.

    Therefore we trust an infobox Production value only when:

    1. The Wikipedia page title explicitly contains one of the
       Variants represented by this scrape,

       OR

    2. The Production value itself explicitly names one of those
       Variants.

    This keeps generation-specific pages usable while preventing
    model-wide infobox values from contaminating individual
    Variants.
    """

    if not variants:
        return []

    production_value = _find_production_value(
        infobox
    )

    if (
        not production_value
        or not re.search(
            r"\b\d{4}\b",
            production_value,
        )
    ):
        return []

    # --------------------------------------------------------
    # CRITICAL SCOPE CHECK
    # --------------------------------------------------------

    if not _production_source_is_variant_scoped(
        soup=soup,
        production_value=production_value,
        variants=variants,
    ):
        return []

    # --------------------------------------------------------
    # Single Variant
    #
    # Once we know the source is scoped correctly, preserve the
    # complete source value.
    #
    # This is important for cases such as:
    #
    #     1938–1941 1945–1950
    #
    # or:
    #
    #     1936–1940 464 produced
    #
    # Canonicalization can later reduce this to years.
    # --------------------------------------------------------

    if len(variants) == 1:
        return [
            {
                "variant": variants[0],
                "production": production_value,
            }
        ]

    # --------------------------------------------------------
    # Multi-Variant page
    # --------------------------------------------------------

    clauses = _extract_period_clauses(
        production_value
    )

    # --------------------------------------------------------
    # One shared production period
    #
    # If Wikipedia gives only one generation-wide period, there
    # is no source evidence for different Variant dates.
    #
    # Example:
    #
    #     G14 / G15 / G16
    #     Production: 2018–2026
    #
    # Copying it to all three is faithful to the source.
    # --------------------------------------------------------

    if len(clauses) <= 1:
        return [
            {
                "variant": variant,
                "production": production_value,
            }
            for variant in variants
        ]

    body_style_by_variant = (
        _build_body_style_lookup(
            variant_body_styles or []
        )
    )

    result = []

    for variant in variants:
        production = _resolve_variant_production(
            variant=variant,
            body_style=body_style_by_variant.get(
                variant
            ),
            clauses=clauses,
        )

        if production is None:
            continue

        result.append(
            {
                "variant": variant,
                "production": production,
            }
        )

    return result


# ============================================================
# Production-field extraction
# ============================================================

def _find_production_value(
    infobox: dict[str, str],
) -> str | None:
    """
    Return ONLY the exact Wikipedia infobox field:

        Production

    Do NOT accept:

        Production location
        Production site
        Production company

    etc.

    This fixes cases such as BMW F 76 where a production-location
    value was previously mistaken for a production period.
    """

    for label, value in infobox.items():
        normalized_label = (
            label.strip().casefold()
        )

        if normalized_label != "production":
            continue

        value = value.strip()

        if value:
            return value

    return None


# ============================================================
# Source-scope validation
# ============================================================

def _production_source_is_variant_scoped(
    soup: BeautifulSoup,
    production_value: str,
    variants: list[str],
) -> bool:
    """
    Decide whether the infobox Production value can safely be
    attached to the Variants being scraped.

    Accept when either:

        A. The Wikipedia article title explicitly names one of
           our Variants.

           Example:
               BMW 5 Series (G60)
               BMW E28
               BMW Z3
               BMW 507

        B. The Production field itself explicitly names one of
           our Variants.

           Example:
               G60: July 2023–present
               G61: March 2024–present

    Reject model-wide pages such as:

        BMW X3
        BMW X6
        BMW X2

    if their Production field contains only lineage-wide dates
    and no explicit Variant identifiers.
    """

    page_title = _get_page_title(
        soup
    )

    if page_title:
        for variant in variants:
            if _variant_is_in_context(
                variant,
                page_title,
            ):
                return True

    # --------------------------------------------------------
    # The page title may be generic, but Wikipedia can still
    # provide explicitly Variant-scoped production data inside
    # the field itself.
    # --------------------------------------------------------

    for variant in variants:
        if _variant_is_in_context(
            variant,
            production_value,
        ):
            return True

    return False


def _get_page_title(
    soup: BeautifulSoup,
) -> str | None:
    """
    Extract a clean Wikipedia article title.
    """

    if soup.title is None:
        return None

    title = soup.title.get_text(
        " ",
        strip=True,
    )

    title = title.removesuffix(
        " - Wikipedia"
    )

    title = title.strip()

    return title or None


# ============================================================
# Production-clause extraction
# ============================================================

def _extract_period_clauses(
    value: str,
) -> list[dict]:
    """
    Break a Production field into individual date periods and
    retain nearby context.

    Example:

        July 2023 – present (sedan)
        March 2024 – present (estate)
        June 2024 – present (M5)

    becomes:

        [
            {
                "period": "July 2023 – present",
                "context": "sedan",
            },
            {
                "period": "March 2024 – present",
                "context": "estate",
            },
            {
                "period": "June 2024 – present",
                "context": "M5",
            },
        ]

    This also supports:

        G60: July 2023 – present
        G61: March 2024 – present

    because text immediately preceding each period is retained
    as context.
    """

    matches = list(
        PRODUCTION_PERIOD_PATTERN.finditer(
            value
        )
    )

    clauses = []

    for index, match in enumerate(matches):
        if index == 0:
            previous_end = 0
        else:
            previous_end = (
                matches[index - 1].end()
            )

        prefix = value[
            previous_end:match.start()
        ]

        prefix = prefix.strip(
            " \t\r\n,;:-"
        )

        qualifier = (
            match.group("qualifier") or ""
        ).strip()

        context_parts = []

        if prefix:
            context_parts.append(
                prefix
            )

        if qualifier:
            context_parts.append(
                qualifier
            )

        context = " ".join(
            context_parts
        ).strip()

        clauses.append(
            {
                "period": match.group(
                    "period"
                ).strip(),
                "context": context,
            }
        )

    return clauses


# ============================================================
# Variant-specific resolution
# ============================================================

def _resolve_variant_production(
    variant: str,
    body_style: str | None,
    clauses: list[dict],
) -> str | None:
    """
    Resolve several production periods to one Variant.

    Evidence priority:

        1. Explicit Variant identifier
        2. Body-style qualifier
        3. One unqualified general period

    If none provides enough evidence, return None.
    """

    # --------------------------------------------------------
    # 1. Explicit Variant code/name
    #
    # Example:
    #
    #     F22: 2013–2021
    #     F23: 2014–2021
    # --------------------------------------------------------

    explicit_matches = [
        clause["period"]
        for clause in clauses
        if _variant_is_in_context(
            variant,
            clause["context"],
        )
    ]

    if explicit_matches:
        return _join_periods(
            explicit_matches
        )

    # --------------------------------------------------------
    # 2. Body style
    #
    # Example:
    #
    #     July 2023 – present (sedan)
    #     March 2024 – present (estate)
    #
    # G60:
    #     4-door saloon
    #
    # G61:
    #     5-door estate
    # --------------------------------------------------------

    if body_style:
        body_terms = _body_style_terms(
            body_style
        )

        style_matches = [
            clause["period"]
            for clause in clauses
            if _context_matches_body_style(
                clause["context"],
                body_terms,
            )
        ]

        if style_matches:
            return _join_periods(
                style_matches
            )

    # --------------------------------------------------------
    # 3. One general/unqualified production period
    #
    # If there is exactly one general period plus additional
    # special derivative periods, the general one can apply to
    # the Variant.
    # --------------------------------------------------------

    unqualified = [
        clause["period"]
        for clause in clauses
        if not clause["context"].strip()
    ]

    if len(unqualified) == 1:
        return unqualified[0]

    # --------------------------------------------------------
    # Ambiguous.
    #
    # Missing data is preferable to inventing an association.
    # --------------------------------------------------------

    return None


# ============================================================
# Body-style matching
# ============================================================

def _build_body_style_lookup(
    variant_body_styles: list[dict],
) -> dict[str, str]:
    """
    Build:

        {
            "G60": "4-door saloon",
            "G61": "5-door estate",
        }
    """

    result = {}

    for item in variant_body_styles:
        variant = item.get(
            "variant"
        )

        body_style = item.get(
            "body_style"
        )

        if (
            not variant
            or not body_style
        ):
            continue

        result[variant] = body_style

    return result


def _body_style_terms(
    value: str,
) -> set[str]:
    """
    Convert raw Wikipedia body-style wording into rough
    semantic categories used only for association.

    Examples:

        4-door saloon
            -> sedan

        5-door estate
            -> wagon

        5-door liftback
            -> fastback

        long-wheelbase sedan
            -> sedan + lwb
    """

    normalized = (
        value.casefold()
        .replace("–", "-")
        .replace("—", "-")
    )

    terms = set()

    for canonical_name, aliases in (
        BODY_STYLE_GROUPS.items()
    ):
        for alias in aliases:
            if _contains_phrase(
                normalized,
                alias.casefold(),
            ):
                terms.add(
                    canonical_name
                )
                break

    return terms


def _context_matches_body_style(
    context: str,
    body_terms: set[str],
) -> bool:
    """
    Compare a Production qualifier with a Variant body style.
    """

    if (
        not context
        or not body_terms
    ):
        return False

    context_terms = _body_style_terms(
        context
    )

    return bool(
        body_terms
        & context_terms
    )


# ============================================================
# Generic matching helpers
# ============================================================

def _variant_is_in_context(
    variant: str,
    context: str,
) -> bool:
    """
    Boundary-aware Variant matching.

    Examples:

        G60 matches:
            BMW 5 Series (G60)
            G60 sedan

        G60 does not match:
            G601

    Also works for historical/non-code names such as:

        507
        Z3
        3/15
        02 Series
    """

    if (
        not variant
        or not context
    ):
        return False

    escaped = re.escape(
        variant
    )

    escaped = escaped.replace(
        r"\ ",
        r"\s+",
    )

    prefix = ""
    suffix = ""

    if variant[0].isalnum():
        prefix = (
            r"(?<![A-Za-z0-9])"
        )

    if variant[-1].isalnum():
        suffix = (
            r"(?![A-Za-z0-9])"
        )

    pattern = (
        prefix
        + escaped
        + suffix
    )

    return (
        re.search(
            pattern,
            context,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Boundary-aware phrase matching.
    """

    pattern = (
        r"(?<![A-Za-z0-9])"
        + re.escape(phrase)
        + r"(?![A-Za-z0-9])"
    )

    return (
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _join_periods(
    periods: list[str],
) -> str:
    """
    Deduplicate production periods while preserving source
    order.

    Normally this returns one period, but several are retained
    if Wikipedia explicitly associates several periods with the
    same Variant.
    """

    result = []

    for period in periods:
        if period not in result:
            result.append(
                period
            )

    return " ".join(
        result
    )