import re


# ============================================================
# Explicit BMW long-wheelbase chassis variants
#
# This is deliberately a small domain-specific override.
#
# We are NOT trying to reconstruct exact body-specific Version
# availability from Wikipedia.
# ============================================================

BMW_LWB_VARIANT_IDS = {
    # 3 Series
    "bmw_3_series_f35",
    "bmw_3_series_g28",

    # 5 Series
    "bmw_5_series_f18",
    "bmw_5_series_g38",
    "bmw_5_series_g68",

    # 7 Series
    "bmw_7_series_e66",
    "bmw_7_series_f02",
    "bmw_7_series_g12",
}


def assign_versions_to_variant(
    raw_versions: list[str],
    current_variant_id: str,
    page_variant_ids: list[str],
) -> list[dict]:
    """
    Decide which page-level Versions should be attached to one
    Variant.

    General rule:

        Wikipedia's extracted Version names remain unchanged.

        If Wikipedia does not explicitly distinguish Versions by
        chassis, sibling Variants simply share them.

    LWB exception:

        On pages containing an explicitly known BMW
        long-wheelbase chassis, LWB designations such as:

            320Li
            320Ld
            740Le

        are separated for the LWB Variant.

    IMPORTANT:

        For NON-LWB Variants, mixed rows are NOT rewritten.

        Example:

            raw:
                "320i / 325Li"

            G20:
                "320i / 325Li"

            G21:
                "320i / 325Li"

            G28:
                "325Li"

        We deliberately keep the original combined name on the
        normal chassis because another distinct source row may
        already be called "320i".

        Renaming the mixed row to "320i" could therefore merge
        two different Wikipedia specifications into one
        canonical Version ID.

    Each result retains raw_name so engine/power lookup can
    continue using the exact extracted Wikipedia value.
    """

    page_has_lwb_variant = any(
        variant_id in BMW_LWB_VARIANT_IDS
        for variant_id in page_variant_ids
    )

    current_is_lwb = (
        current_variant_id
        in BMW_LWB_VARIANT_IDS
    )

    result = []
    seen_names = set()

    for raw_version in raw_versions:

        # ----------------------------------------------------
        # No LWB chassis on this page.
        #
        # Do nothing special.
        # ----------------------------------------------------

        if not page_has_lwb_variant:
            _append_assignment(
                result=result,
                seen_names=seen_names,
                raw_name=raw_version,
                canonical_name=raw_version,
            )
            continue

        # ----------------------------------------------------
        # Mixed normal/LWB row.
        #
        # Examples:
        #
        #     318i / 320Li
        #     320d / 320Ld
        #     730i/Li
        # ----------------------------------------------------

        split_pair = _split_standard_lwb_pair(
            raw_version
        )

        if split_pair is not None:
            _, lwb_name = split_pair

            if current_is_lwb:
                # LWB chassis gets only the explicitly
                # distinguishable LWB designation.
                canonical_name = lwb_name

            else:
                # Do NOT rename the normal side.
                #
                # Keeping the original source row avoids
                # collapsing it with another independent row
                # that may already have that normal name.
                canonical_name = raw_version

            _append_assignment(
                result=result,
                seen_names=seen_names,
                raw_name=raw_version,
                canonical_name=canonical_name,
            )

            continue

        # ----------------------------------------------------
        # Explicit LWB-only Version.
        #
        # Example:
        #
        #     530Li
        #
        # Only attach it to the LWB chassis.
        # ----------------------------------------------------

        if _contains_lwb_designation(
            raw_version
        ):
            if current_is_lwb:
                _append_assignment(
                    result=result,
                    seen_names=seen_names,
                    raw_name=raw_version,
                    canonical_name=raw_version,
                )

            continue

        # ----------------------------------------------------
        # Generic Version.
        #
        # Wikipedia gives us no useful chassis distinction, so
        # share it between sibling Variants.
        # ----------------------------------------------------

        _append_assignment(
            result=result,
            seen_names=seen_names,
            raw_name=raw_version,
            canonical_name=raw_version,
        )

    return result


def _split_standard_lwb_pair(
    value: str,
) -> tuple[str, str] | None:
    """
    Detect a mixed normal/LWB Version row.

    Examples:

        "318i / 320Li"
            ->
        ("318i", "320Li")


        "320d / 320Ld [ c ]"
            ->
        ("320d", "320Ld")


        "730i/Li"
            ->
        ("730i", "730Li")


        "760i/Li**"
            ->
        ("760i", "760Li")

    Returns None when the slash is not clearly describing one
    normal and one LWB designation.
    """

    cleaned = _clean_for_assignment(
        value
    )

    parts = re.split(
        r"\s*/\s*",
        cleaned,
    )

    if len(parts) != 2:
        return None

    left = parts[0].strip()
    right = parts[1].strip()

    if not left or not right:
        return None

    # --------------------------------------------------------
    # BMW sometimes abbreviates:
    #
    #     730i/Li
    #
    # instead of:
    #
    #     730i/730Li
    # --------------------------------------------------------

    shorthand_match = re.fullmatch(
        r"L([ide])",
        right,
        flags=re.IGNORECASE,
    )

    if shorthand_match:
        number_match = re.match(
            r"(\d{2,4})",
            left,
        )

        if number_match:
            right = (
                number_match.group(1)
                + "L"
                + shorthand_match.group(1)
            )

    left_is_lwb = (
        _contains_lwb_designation(
            left
        )
    )

    right_is_lwb = (
        _contains_lwb_designation(
            right
        )
    )

    # Exactly one side must be recognizably LWB.
    if left_is_lwb == right_is_lwb:
        return None

    if left_is_lwb:
        return (
            right,
            left,
        )

    return (
        left,
        right,
    )


def _contains_lwb_designation(
    value: str,
) -> bool:
    """
    Detect an explicit BMW long-wheelbase marketed designation.

    Examples:

        320Li
        320Ld
        740Le
        750Li xDrive
    """

    cleaned = _clean_for_assignment(
        value
    )

    return bool(
        re.search(
            r"\b\d{2,4}L[ide]\b",
            cleaned,
            flags=re.IGNORECASE,
        )
    )


def _clean_for_assignment(
    value: str,
) -> str:
    """
    Remove annotations that interfere with LWB detection.

    This is only used internally for detection and does not
    replace normal canonical Version cleanup.
    """

    value = re.sub(
        r"\s*\[\s*[^\]]+\s*\]\s*",
        " ",
        value,
    )

    value = re.sub(
        r"[*†‡]+",
        "",
        value,
    )

    return " ".join(
        value.split()
    )


def _append_assignment(
    result: list[dict],
    seen_names: set[str],
    raw_name: str,
    canonical_name: str,
) -> None:
    """
    Add one Version assignment without duplicating the same
    canonical Version name inside one Variant.
    """

    key = (
        canonical_name
        .casefold()
        .strip()
    )

    if not key:
        return

    if key in seen_names:
        return

    seen_names.add(
        key
    )

    result.append(
        {
            "raw_name": raw_name,
            "name": canonical_name,
        }
    )