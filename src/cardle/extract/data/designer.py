import re

from bs4 import BeautifulSoup, NavigableString


DESIGNER_LABELS = {
    "designer",
    "designers",
}

DESIGNER_BREAK = "|||CARDLE_DESIGNER_BREAK|||"


# ============================================================
# Body-style vocabulary
#
# Used ONLY for associating a designer annotation with the
# correct Variant.
#
# These are not canonical Cardle body-style values.
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
        "shooting brake",
        "shooting-brake",
    },
    "coupe": {
        "coupe",
        "coupé",
    },
    "convertible": {
        "convertible",
        "cabriolet",
        "roadster",
    },
    "hatchback": {
        "hatchback",
        "hatch",
    },
    "fastback": {
        "fastback",
        "liftback",
        "gran turismo",
        "gran coupé",
        "gran coupe",
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


def extract_variant_designers(
    soup: BeautifulSoup,
    infobox: dict[str, str],
    variants: list[str],
    variant_body_styles: list[dict] | None = None,
) -> list[dict]:
    """
    Extract designers and associate them with Variants.

    Evidence priority:

        1. Explicit Variant code/name
        2. Explicit body-style qualifier
        3. Generation-wide assignment

    Examples:

        Michael de Bono (F31, 2009)
            -> F31 only

        Joji Nagashima (saloon and estate)
            -> sedan + wagon Variants

        Marc Michael Markefka
            -> all represented Variants

    Designer boundaries are read directly from the HTML so that
    Wikipedia line/list structure is not destroyed by generic
    infobox flattening.
    """

    if not variants:
        return []

    designers = _extract_designer_items_from_html(
        soup
    )

    # --------------------------------------------------------
    # Fallback for unusual infobox markup.
    # --------------------------------------------------------

    if not designers:
        raw_value = _find_designer_value(
            infobox
        )

        if raw_value:
            designers = _split_designer_text(
                raw_value
            )

    if not designers:
        return []

    body_styles_by_variant = (
        _build_body_style_terms_by_variant(
            variant_body_styles or []
        )
    )

    return _associate_designers_with_variants(
        designers=designers,
        variants=variants,
        body_styles_by_variant=body_styles_by_variant,
    )


# ============================================================
# HTML extraction
# ============================================================

def _extract_designer_items_from_html(
    soup: BeautifulSoup,
) -> list[str]:
    """
    Read the Designer cell directly from the Wikipedia infobox.

    Structural boundaries such as <br> and <li> are preserved
    before text extraction.
    """

    designer_cell = _find_designer_cell(
        soup
    )

    if designer_cell is None:
        return []

    # Work on a copy so the main BeautifulSoup tree is never
    # modified.
    fragment = BeautifulSoup(
        str(designer_cell),
        "html.parser",
    )

    # Remove references/citations.
    for sup in fragment.find_all("sup"):
        sup.decompose()

    # Preserve explicit line breaks.
    for br in fragment.find_all("br"):
        br.replace_with(
            NavigableString(
                f" {DESIGNER_BREAK} "
            )
        )

    # Preserve list boundaries.
    for item in fragment.find_all("li"):
        item.insert_before(
            NavigableString(
                f" {DESIGNER_BREAK} "
            )
        )

        item.insert_after(
            NavigableString(
                f" {DESIGNER_BREAK} "
            )
        )

    text = fragment.get_text(
        " ",
        strip=True,
    )

    return _split_designer_text(
        text
    )


def _find_designer_cell(
    soup: BeautifulSoup,
):
    """
    Find the infobox value cell belonging to Designer.
    """

    infobox = soup.select_one(
        "table.infobox"
    )

    if infobox is None:
        return None

    for row in infobox.select("tr"):
        label_cell = row.find("th")
        value_cell = row.find("td")

        if (
            label_cell is None
            or value_cell is None
        ):
            continue

        label = _normalize_text(
            label_cell.get_text(
                " ",
                strip=True,
            )
        ).casefold()

        if label in DESIGNER_LABELS:
            return value_cell

    return None


# ============================================================
# Flattened-infobox fallback
# ============================================================

def _find_designer_value(
    infobox: dict[str, str],
) -> str | None:
    """
    Find Designer in the generic flattened infobox.
    """

    for label, value in infobox.items():
        if (
            label.strip().casefold()
            not in DESIGNER_LABELS
        ):
            continue

        value = value.strip()

        if value:
            return value

    return None


# ============================================================
# Designer splitting
# ============================================================

def _split_designer_text(
    value: str,
) -> list[str]:
    """
    Split designer text only at boundaries supported by the
    source:

        - preserved HTML line/list boundaries
        - commas outside parentheses
        - semicolons outside parentheses

    We never infer name boundaries from capitalization.
    """

    if not value:
        return []

    # Remove citation markers from fallback text.
    value = re.sub(
        r"\s*\[\s*(?:\d+|citation needed)\s*\]\s*",
        " ",
        value,
        flags=re.IGNORECASE,
    )

    chunks = value.split(
        DESIGNER_BREAK
    )

    result = []

    for chunk in chunks:
        chunk = _normalize_text(
            chunk
        )

        if not chunk:
            continue

        parts = _split_top_level_punctuation(
            chunk
        )

        for part in parts:
            part = _clean_designer_item(
                part
            )

            if (
                part
                and part not in result
            ):
                result.append(
                    part
                )

    return result


def _split_top_level_punctuation(
    value: str,
) -> list[str]:
    """
    Split commas and semicolons only outside parentheses.

    Example:

        Chris Bangle (1996, LCI: 2002), Frank Stephenson

    becomes:

        Chris Bangle (1996, LCI: 2002)
        Frank Stephenson
    """

    result = []
    current = []

    parentheses_depth = 0
    brackets_depth = 0

    for character in value:

        if character == "(":
            parentheses_depth += 1

        elif character == ")":
            parentheses_depth = max(
                0,
                parentheses_depth - 1,
            )

        elif character == "[":
            brackets_depth += 1

        elif character == "]":
            brackets_depth = max(
                0,
                brackets_depth - 1,
            )

        if (
            character in {",", ";"}
            and parentheses_depth == 0
            and brackets_depth == 0
        ):
            part = _normalize_text(
                "".join(current)
            )

            if part:
                result.append(
                    part
                )

            current = []
            continue

        current.append(
            character
        )

    final_part = _normalize_text(
        "".join(current)
    )

    if final_part:
        result.append(
            final_part
        )

    return result


def _clean_designer_item(
    value: str,
) -> str:
    """
    Light raw-data cleanup.

    Role/body/year annotations remain intact for canonicalization.
    """

    value = _normalize_text(
        value
    )

    return value.strip(
        " ,;|-–—"
    )


# ============================================================
# Variant association
# ============================================================

def _associate_designers_with_variants(
    designers: list[str],
    variants: list[str],
    body_styles_by_variant: dict[str, set[str]],
) -> list[dict]:
    """
    Associate each designer using progressively weaker evidence.

    Priority:

        1. Explicit Variant
        2. Body style
        3. Generation-wide
    """

    result = []

    for designer in designers:

        # ----------------------------------------------------
        # 1. Explicit Variant identifier
        #
        # Example:
        #
        #     Michael de Bono (F31, 2009)
        # ----------------------------------------------------

        explicit_variants = [
            variant
            for variant in variants
            if _variant_is_in_context(
                variant,
                designer,
            )
        ]

        if explicit_variants:
            targets = explicit_variants

        else:

            # ------------------------------------------------
            # 2. Explicit body-style annotation
            #
            # Examples:
            #
            #     Joji Nagashima (saloon and estate)
            #
            #     Marc Michael Markefka
            #         (coupé and convertible)
            #
            #     Jean-Francois Huet (Touring)
            # ------------------------------------------------

            designer_body_terms = (
                _body_style_terms(
                    designer
                )
            )

            style_targets = []

            if designer_body_terms:
                for variant in variants:
                    variant_terms = (
                        body_styles_by_variant.get(
                            variant,
                            set(),
                        )
                    )

                    if (
                        designer_body_terms
                        & variant_terms
                    ):
                        style_targets.append(
                            variant
                        )

            if style_targets:
                targets = style_targets

            else:

                # --------------------------------------------
                # 3. No usable Variant/body-style evidence.
                #
                # Treat as generation-wide.
                # --------------------------------------------

                targets = variants

        for variant in targets:
            item = {
                "variant": variant,
                "designer": designer,
            }

            if item not in result:
                result.append(
                    item
                )

    return result


# ============================================================
# Variant body-style lookup
# ============================================================

def _build_body_style_terms_by_variant(
    variant_body_styles: list[dict],
) -> dict[str, set[str]]:
    """
    Build semantic body-style sets for each Variant.

    Example:

        G20 -> {"sedan"}
        G21 -> {"wagon"}

        E46 -> {
            "sedan",
            "wagon",
            "coupe",
            "convertible",
            "hatchback",
        }
    """

    result: dict[str, set[str]] = {}

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

        result.setdefault(
            variant,
            set(),
        ).update(
            _body_style_terms(
                body_style
            )
        )

    return result


def _body_style_terms(
    value: str,
) -> set[str]:
    """
    Convert raw wording into semantic body-style categories.

    Examples:

        "4-door saloon"
            -> {"sedan"}

        "5-door estate"
            -> {"wagon"}

        "saloon and estate"
            -> {"sedan", "wagon"}

        "coupé and convertible"
            -> {"coupe", "convertible"}

        "Gran Turismo"
            -> {"fastback"}
    """

    if not value:
        return set()

    normalized = (
        value.casefold()
        .replace("–", "-")
        .replace("—", "-")
    )

    result = set()

    for canonical_name, aliases in (
        BODY_STYLE_GROUPS.items()
    ):
        for alias in aliases:
            if _contains_phrase(
                normalized,
                alias.casefold(),
            ):
                result.add(
                    canonical_name
                )
                break

    return result


# ============================================================
# Generic matching helpers
# ============================================================

def _variant_is_in_context(
    variant: str,
    context: str,
) -> bool:
    """
    Boundary-aware Variant matching.

    Example:

        F31 matches:
            "Michael de Bono (F31, 2009)"

        but not:
            "F310"
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


def _normalize_text(
    value: str,
) -> str:
    """
    Collapse repeated whitespace.
    """

    return " ".join(
        value.split()
    )