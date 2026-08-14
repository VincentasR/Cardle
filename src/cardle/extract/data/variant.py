import re

from bs4 import BeautifulSoup


# ---------------------------------------------------------
# Variant-code recognition
#
# Intentionally conservative:
# - must contain at least one letter
# - must contain at least one digit
#
# Examples:
#     E60
#     G20
#     G28
#     U11
#     I01
#     NA0
#
# This avoids accidentally treating things such as:
#     2024
#     Sedan
#     Gran Coupé
#
# as manufacturer codes.
# ---------------------------------------------------------

VARIANT_CODE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"([A-Za-z]{1,4}\d[A-Za-z0-9-]{0,8})"
    r"(?![A-Za-z0-9])"
)


BODY_STYLE_KEYS = {
    "body style",
    "body styles",
}


def get_page_title(
    soup: BeautifulSoup,
) -> str | None:
    """
    Return the Wikipedia article title without
    the Wikipedia suffix.
    """

    if soup.title is None:
        return None

    title = soup.title.get_text(
        " ",
        strip=True,
    )

    return title.removesuffix(
        " - Wikipedia"
    ).strip()


def remove_manufacturer_prefix(
    title: str,
    manufacturer: str,
) -> str:
    """
    Remove the manufacturer from the beginning
    of a title.

    Example:
        BMW 507 -> 507
    """

    if title.casefold().startswith(
        manufacturer.casefold()
    ):
        return title[
            len(manufacturer):
        ].strip()

    return title.strip()


def split_variant_codes(
    raw_value: str,
) -> list[str]:
    """
    Extract manufacturer/body codes from text.

    Examples:
        E63/E64
            -> ["E63", "E64"]

        F12/F13/F06
            -> ["F12", "F13", "F06"]

        G20/G28
            -> ["G20", "G28"]

        G26, Gran Coupé
            -> ["G26"]

        G20
            -> ["G20"]
    """

    return VARIANT_CODE_PATTERN.findall(
        raw_value
    )


def extract_variants(
    soup: BeautifulSoup,
    manufacturer: str,
    discovery_name: str | None = None,
    model: str | None = None,
    infobox: dict[str, str] | None = None,
) -> list[str]:
    """
    Extract the Variant/body codes represented
    by a Wikipedia vehicle page.

    Sources are considered in this order:

    1. Parenthesized codes in the discovery label.
    2. Parenthesized codes in the Wikipedia title.
    3. A bare discovery label when it itself looks
       like a manufacturer code.
    4. Explicit body-code annotations in the
       infobox Body style field.
    5. For "No Model" vehicles, fall back to the
       vehicle title/name.

    Important:
    Body-style fields are only used when they
    explicitly contain code-like labels. We do
    not infer missing body codes from body-style
    words alone.
    """

    variants: list[str] = []

    page_title = get_page_title(
        soup
    )

    # -----------------------------------------------------
    # 1. Discovery label
    #
    # Example:
    #     6 Series (E63/E64)
    # -----------------------------------------------------

    if discovery_name:
        _append_codes_from_trailing_parentheses(
            variants,
            discovery_name,
        )

    # -----------------------------------------------------
    # 2. Wikipedia page title
    #
    # Example:
    #     BMW 4 Series (G22)
    # -----------------------------------------------------

    if page_title:
        _append_codes_from_trailing_parentheses(
            variants,
            page_title,
        )

    # -----------------------------------------------------
    # 3. Bare discovery code
    #
    # Some discovery records are simply:
    #
    #     G45
    #     U10
    #     F70
    #
    # Use this only when the complete discovery
    # string itself is a code.
    # -----------------------------------------------------

    if discovery_name:
        discovery_value = discovery_name.strip()

        if VARIANT_CODE_PATTERN.fullmatch(
            discovery_value
        ):
            _append_unique(
                variants,
                discovery_value,
            )

    # -----------------------------------------------------
    # 4. Explicit body-code annotations from infobox
    #
    # Examples:
    #
    # 4-door sedan (G20/G28)
    # 5-door wagon (G21)
    #
    # 2-door coupé (G22)
    # 2-door convertible (G23)
    # 5-door liftback (G26, Gran Coupé)
    #
    # We only inspect parenthetical groups. This prevents
    # unrelated numbers elsewhere in the body-style text
    # from becoming Variants.
    # -----------------------------------------------------

    if infobox:
        for label, value in infobox.items():
            if label.casefold().strip() not in BODY_STYLE_KEYS:
                continue

            for group in _extract_parenthetical_groups(
                value
            ):
                codes = split_variant_codes(
                    group
                )

                for code in codes:
                    _append_unique(
                        variants,
                        code,
                    )

    # -----------------------------------------------------
    # If we found actual manufacturer/body codes,
    # return them now.
    # -----------------------------------------------------

    if variants:
        return variants

    # -----------------------------------------------------
    # 5. Vehicles with no separate Model
    #
    # Examples:
    #     BMW 507
    #     BMW Z1
    #     BMW 3/15
    #
    # These do not have to match the manufacturer-code
    # pattern.
    # -----------------------------------------------------

    if model == "No Model":
        fallback = discovery_name

        if not fallback and page_title:
            fallback = remove_manufacturer_prefix(
                page_title,
                manufacturer,
            )

        if fallback:
            fallback = re.sub(
                r"\s+\((?:"
                r"sedans?|"
                r"coupés?|"
                r"coupes?"
                r")\)\s*$",
                "",
                fallback,
                flags=re.IGNORECASE,
            ).strip()

            if fallback:
                return [fallback]

    return []


def _append_codes_from_trailing_parentheses(
    variants: list[str],
    value: str,
) -> None:
    """
    Extract code-like values from trailing parentheses.

    Examples:
        "6 Series (E63/E64)"
        "BMW X3 (G01)"
    """

    match = re.search(
        r"\(([^()]*)\)\s*$",
        value,
    )

    if match is None:
        return

    raw_value = match.group(1).strip()

    codes = split_variant_codes(
        raw_value
    )

    for code in codes:
        _append_unique(
            variants,
            code,
        )


def _extract_parenthetical_groups(
    value: str,
) -> list[str]:
    """
    Return every non-nested parenthetical group.

    Example:

        "4-door sedan (G20/G28) "
        "5-door wagon (G21)"

    becomes:

        ["G20/G28", "G21"]
    """

    return re.findall(
        r"\(([^()]*)\)",
        value,
    )


def _append_unique(
    values: list[str],
    value: str,
) -> None:
    """
    Append a value while preserving source order.
    """

    if value not in values:
        values.append(value)