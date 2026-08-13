from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag


BODY_STYLE_LABELS = {
    "body style",
    "body styles",
}

MODEL_CODE_LABELS = {
    "model code",
    "model codes",
}


# These are only used when Wikipedia puts the body description
# inside the Model code field:
#
#     E63 (Coupe)
#     F45 (Active Tourer)
#
# They prevent unrelated descriptions such as:
#
#     E65 (short-wheelbase)
#
# from being treated as body styles.
BODY_STYLE_TERMS = {
    "coupe",
    "coupé",
    "convertible",
    "cabriolet",
    "roadster",
    "sedan",
    "saloon",
    "wagon",
    "estate",
    "touring",
    "hatchback",
    "fastback",
    "liftback",
    "shooting brake",
    "shooting-brake",
    "suv",
    "crossover",
    "pickup",
    "pick-up",
    "van",
    "mpv",
    "active tourer",
    "gran tourer",
    "gran turismo",
}


def _normalize_text(text: str) -> str:
    """
    Collapse repeated whitespace while preserving the original wording.
    """

    return " ".join(
        text.split()
    )


def _normalize_label(text: str) -> str:
    return _normalize_text(
        text
    ).casefold()


def _contains_variant(
    text: str,
    variant: str,
) -> bool:
    """
    Check whether a variant occurs as a distinct token.

    Example:
        F10 matches "(F10)"
        F1 does not accidentally match "F10"
    """

    pattern = (
        r"(?<![A-Za-z0-9])"
        + re.escape(variant)
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


def _find_value_cell(
    infobox: Tag,
    labels: set[str],
) -> Tag | None:
    """
    Find the value <td> for a particular infobox field.
    """

    for row in infobox.find_all(
        "tr",
        recursive=True,
    ):
        header = row.find(
            "th",
            recursive=False,
        )

        value = row.find(
            "td",
            recursive=False,
        )

        if header is None or value is None:
            continue

        label = _normalize_label(
            header.get_text(
                " ",
                strip=True,
            )
        )

        if label in labels:
            return value

    return None


def _get_infoboxes(
    soup: BeautifulSoup,
) -> list[Tag]:
    """
    Return every Wikipedia infobox on the page.

    This is important for articles containing several generations.
    A generation-specific infobox may not be the first infobox.
    """

    return list(
        soup.select(
            "table.infobox"
        )
    )


def _looks_like_body_style(
    text: str,
) -> bool:
    """
    Conservative check for descriptions taken from Model code.

    Model-code annotations are not always body styles.

    Good:
        Coupe
        Convertible
        Saloon
        Touring
        Active Tourer
        Gran Tourer

    Bad:
        short-wheelbase
        long-wheelbase
    """

    normalized = (
        _normalize_text(text)
        .casefold()
    )

    return any(
        term in normalized
        for term in BODY_STYLE_TERMS
    )


def _clean_body_style(
    text: str,
) -> str:
    """
    Basic whitespace cleanup only.

    Do NOT canonicalize terms here.
    """

    text = _normalize_text(text)

    # Remove simple separators that may remain between entries.
    text = text.strip(
        " ,;/–—-"
    )

    return _normalize_text(text)


def _variant_group_pattern(
    variants: list[str],
) -> re.Pattern | None:
    """
    Build a regex that finds parenthetical groups containing
    one or more known variants.

    Examples:

        (E60)
        (F10)
        (G20/G28)

    We intentionally use only the variants already discovered
    for this vehicle.
    """

    if not variants:
        return None

    escaped = sorted(
        (
            re.escape(variant)
            for variant in variants
        ),
        key=len,
        reverse=True,
    )

    alternatives = "|".join(
        escaped
    )

    return re.compile(
        rf"\(([^)]*(?:{alternatives})[^)]*)\)",
        flags=re.IGNORECASE,
    )


def _variants_in_annotation(
    annotation: str,
    variants: list[str],
) -> list[str]:
    """
    Determine which requested variants are explicitly mentioned
    inside a parenthetical annotation.

    Example:

        annotation = "G20/G28"

        -> ["G20", "G28"]
    """

    return [
        variant
        for variant in variants
        if _contains_variant(
            annotation,
            variant,
        )
    ]


def _extract_from_body_style_cell(
    cell: Tag,
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Parse explicit body-style -> variant associations.

    Supports:

        4-door sedan (E60)
        5-door wagon (E61)

    and:

        4-door sedan (F10)
        4-door LWB sedan (F18)
        5-door wagon (F11)
        5-door fastback (F07)

    It does not rely on <br> tags being preserved correctly.
    """

    text = cell.get_text(
        " ",
        strip=True,
    )

    text = _normalize_text(
        text
    )

    pattern = _variant_group_pattern(
        variants
    )

    if pattern is None:
        return []

    matches = list(
        pattern.finditer(text)
    )

    if not matches:
        return []

    results: list[dict[str, str]] = []

    previous_end = 0

    for match in matches:
        body_style = text[
            previous_end:match.start()
        ]

        body_style = _clean_body_style(
            body_style
        )

        annotation = match.group(1)

        matched_variants = (
            _variants_in_annotation(
                annotation=annotation,
                variants=variants,
            )
        )

        if (
            body_style
            and matched_variants
        ):
            for variant in matched_variants:
                results.append(
                    {
                        "variant": variant,
                        "body_style": body_style,
                    }
                )

        previous_end = match.end()

    return results


def _extract_from_model_code_cell(
    cell: Tag,
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Parse explicit variant -> description associations in Model code.

    Examples:

        E63 (Coupe)
        E64 (Convertible)

        F45 (Active Tourer)
        F46 (Gran Tourer)

    Descriptions are accepted only when they resemble a body style.
    This deliberately rejects things such as:

        E65 (short-wheelbase)
        E66 (long-wheelbase)
    """

    text = cell.get_text(
        " ",
        strip=True,
    )

    text = _normalize_text(
        text
    )

    results: list[dict[str, str]] = []

    for variant in variants:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9])"
            rf"{re.escape(variant)}"
            rf"(?![A-Za-z0-9])"
            rf"\s*\(([^()]*)\)",
            flags=re.IGNORECASE,
        )

        match = pattern.search(
            text
        )

        if match is None:
            continue

        body_style = _clean_body_style(
            match.group(1)
        )

        if not body_style:
            continue

        if not _looks_like_body_style(
            body_style
        ):
            continue

        results.append(
            {
                "variant": variant,
                "body_style": body_style,
            }
        )

    return results


def _deduplicate(
    mappings: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Remove duplicate variant/body-style mappings while preserving order.
    """

    results: list[
        dict[str, str]
    ] = []

    seen: set[
        tuple[str, str]
    ] = set()

    for mapping in mappings:
        key = (
            mapping["variant"],
            mapping["body_style"],
        )

        if key in seen:
            continue

        seen.add(key)
        results.append(
            mapping
        )

    return results


def _extract_explicit_body_style_mappings(
    soup: BeautifulSoup,
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Search all infoboxes for explicit mappings.

    Priority:

    1. Body style
       Strongest evidence because Wikipedia explicitly calls
       the value a body style.

    2. Model code
       Used only when the parenthetical description looks like
       a body style.
    """

    infoboxes = _get_infoboxes(
        soup
    )

    # ---------------------------------------------------------
    # 1. BODY STYLE FIELD
    # ---------------------------------------------------------

    body_style_results: list[
        dict[str, str]
    ] = []

    for box in infoboxes:
        cell = _find_value_cell(
            infobox=box,
            labels=BODY_STYLE_LABELS,
        )

        if cell is None:
            continue

        mappings = (
            _extract_from_body_style_cell(
                cell=cell,
                variants=variants,
            )
        )

        body_style_results.extend(
            mappings
        )

    body_style_results = _deduplicate(
        body_style_results
    )

    if body_style_results:
        return body_style_results

    # ---------------------------------------------------------
    # 2. MODEL CODE FALLBACK
    # ---------------------------------------------------------

    model_code_results: list[
        dict[str, str]
    ] = []

    for box in infoboxes:
        cell = _find_value_cell(
            infobox=box,
            labels=MODEL_CODE_LABELS,
        )

        if cell is None:
            continue

        mappings = (
            _extract_from_model_code_cell(
                cell=cell,
                variants=variants,
            )
        )

        model_code_results.extend(
            mappings
        )

    return _deduplicate(
        model_code_results
    )


def extract_variant_body_styles(
    soup: BeautifulSoup,
    infobox: dict[str, str],
    variants: list[str],
) -> list[dict[str, str]]:
    """
    Extract raw variant/body-style information.

    Rules:

    SINGLE VARIANT
    --------------
    Preserve the previous scraper behavior:
    copy the raw Body style field onto that variant.

    MULTIPLE VARIANTS
    -----------------
    Only create relationships when Wikipedia explicitly provides
    the association.

    Preferred form:

        Body style:
            4-door sedan (E60)
            5-door wagon (E61)

    Fallback form:

        Model code:
            E63 (Coupe)
            E64 (Convertible)

    If Wikipedia does not explicitly associate a body style with
    the variants, return [] rather than inventing relationships.
    """

    if not variants:
        return []

    # ---------------------------------------------------------
    # SINGLE VARIANT
    #
    # Preserve existing behavior exactly.
    # ---------------------------------------------------------

    if len(variants) == 1:
        body_style = None

        for key, value in infobox.items():
            normalized_key = (
                key.strip()
                .casefold()
            )

            if normalized_key in BODY_STYLE_LABELS:
                body_style = value
                break

        if not body_style:
            return []

        return [
            {
                "variant": variants[0],
                "body_style": body_style,
            }
        ]

    # ---------------------------------------------------------
    # MULTIPLE VARIANTS
    #
    # Do not guess.
    # ---------------------------------------------------------

    return (
        _extract_explicit_body_style_mappings(
            soup=soup,
            variants=variants,
        )
    )