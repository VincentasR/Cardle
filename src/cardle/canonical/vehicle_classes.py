import re


VEHICLE_CLASS_ALIASES = {
    "Subcompact luxury crossover SUV": [
        "subcompact luxury crossover suv",
    ],
    "Compact luxury crossover SUV": [
        "compact luxury crossover suv",
    ],
    "Mid-size luxury crossover SUV": [
        "mid-size luxury crossover suv",
        "midsize luxury crossover suv",
        "mid size luxury crossover suv",
    ],
    "Full-size luxury car": [
        "full-size luxury car",
        "full size luxury car",
    ],
    "Subcompact executive car": [
        "subcompact executive car",
    ],
    "Compact executive car": [
        "compact executive car",
    ],
    "Small family car": [
        "small family car",
    ],
    "Mid-size car": [
        "mid-size car",
        "midsize car",
        "mid size car",
    ],
    "Executive car": [
        "executive car",
    ],
    "Luxury car": [
        "luxury car",
    ],
    "Grand tourer": [
        "grand tourer",
        "grand touring",
        "gt car",
    ],
    "Sports car": [
        "sports car",
    ],
    "City car": [
        "city car",
    ],
    "Roadster": [
        "roadster",
    ],
}


def parse_vehicle_classes(value: str) -> list[str]:
    """
    Parse raw Wikipedia vehicle-class text into canonical
    Cardle vehicle classes.

    More specific classes take priority over shorter classes
    contained inside them.

    Examples:
        "Compact executive car (D)"
            -> ["Compact executive car"]

        "Subcompact executive car"
            -> ["Subcompact executive car"]

        "Full-size luxury car (F)"
            -> ["Full-size luxury car"]

        "Grand tourer Executive car"
            -> ["Grand tourer", "Executive car"]
    """

    if not value:
        return []

    value_lower = _normalize(value)

    matches = []

    # ---------------------------------------------------------
    # Find every possible alias match.
    # ---------------------------------------------------------

    for canonical_name, aliases in VEHICLE_CLASS_ALIASES.items():
        for alias in aliases:
            alias_normalized = _normalize(alias)

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias_normalized)
                + r"(?![a-z0-9])"
            )

            for match in re.finditer(
                pattern,
                value_lower,
            ):
                matches.append(
                    {
                        "canonical_name": canonical_name,
                        "start": match.start(),
                        "end": match.end(),
                        "length": match.end() - match.start(),
                    }
                )

    # ---------------------------------------------------------
    # Prefer the longest / most specific matches.
    #
    # Example:
    #
    #   "compact executive car"
    #
    # produces possible matches for:
    #
    #   Compact executive car
    #   Executive car
    #
    # We keep only the longer one because their text spans
    # overlap.
    # ---------------------------------------------------------

    matches.sort(
        key=lambda item: (
            -item["length"],
            item["start"],
        )
    )

    selected = []

    for candidate in matches:
        overlaps = False

        for existing in selected:
            if _spans_overlap(
                candidate["start"],
                candidate["end"],
                existing["start"],
                existing["end"],
            ):
                overlaps = True
                break

        if not overlaps:
            selected.append(candidate)

    # Restore source-text order.
    selected.sort(
        key=lambda item: item["start"]
    )

    result = []

    for match in selected:
        canonical_name = match["canonical_name"]

        if canonical_name not in result:
            result.append(canonical_name)

    return result


def _normalize(value: str) -> str:
    """
    Normalize text enough for alias matching without changing
    the meaning of the source value.
    """

    value = value.lower()

    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def _spans_overlap(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return (
        start_a < end_b
        and start_b < end_a
    )