import re


def parse_layout(value: str) -> tuple[list[str], list[str]]:
    """
    Parse a raw vehicle layout string into canonical
    engine-position and drivetrain values.

    Examples:
        "Front-engine, rear-wheel-drive"
            -> ["Front"], ["RWD"]

        "Rear-wheel drive"
            -> [], ["RWD"]

        "Front-engine, front-wheel-drive
         Front-engine, all-wheel-drive (xDrive)"
            -> ["Front"], ["FWD", "AWD"]

        "FR"
            -> ["Front"], ["RWD"]
    """

    if not value:
        return [], []

    value_lower = value.lower()

    engine_positions = []
    drivetrains = []

    # ---------------------------------------------------------
    # Engine position
    # ---------------------------------------------------------

    if (
        "front-engine" in value_lower
        or "front engine" in value_lower
    ):
        _append_unique(
            engine_positions,
            "Front",
        )

    if (
        "mid-engine" in value_lower
        or "mid engine" in value_lower
    ):
        _append_unique(
            engine_positions,
            "Mid",
        )

    if (
        "rear-engine" in value_lower
        or "rear engine" in value_lower
    ):
        _append_unique(
            engine_positions,
            "Rear",
        )

    # ---------------------------------------------------------
    # Drivetrain
    # ---------------------------------------------------------

    if (
        "front-wheel-drive" in value_lower
        or "front-wheel drive" in value_lower
        or "front wheel drive" in value_lower
    ):
        _append_unique(
            drivetrains,
            "FWD",
        )

    if (
        "rear-wheel-drive" in value_lower
        or "rear-wheel drive" in value_lower
        or "rear wheel drive" in value_lower
    ):
        _append_unique(
            drivetrains,
            "RWD",
        )

    if (
        "all-wheel-drive" in value_lower
        or "all-wheel drive" in value_lower
        or "all wheel drive" in value_lower
        or "four-wheel-drive" in value_lower
        or "four-wheel drive" in value_lower
        or "four wheel drive" in value_lower
        or "4-wheel-drive" in value_lower
        or "4-wheel drive" in value_lower
        or "4 wheel drive" in value_lower
        or "xdrive" in value_lower
    ):
        _append_unique(
            drivetrains,
            "AWD",
        )

    # ---------------------------------------------------------
    # Compact layout abbreviations
    #
    # IMPORTANT:
    # These must be matched as standalone tokens.
    #
    # Using startswith("fr") would incorrectly interpret:
    #
    #     "front-engine..."
    #
    # as the abbreviation FR.
    # ---------------------------------------------------------

    abbreviations = {
        "fr": ("Front", "RWD"),
        "ff": ("Front", "FWD"),
        "mr": ("Mid", "RWD"),
        "rr": ("Rear", "RWD"),
        "f4": ("Front", "AWD"),
        "m4": ("Mid", "AWD"),
        "r4": ("Rear", "AWD"),
    }

    for abbreviation, (
        engine_position,
        drivetrain,
    ) in abbreviations.items():

        pattern = rf"\b{re.escape(abbreviation)}\b"

        if re.search(
            pattern,
            value_lower,
        ):
            _append_unique(
                engine_positions,
                engine_position,
            )

            _append_unique(
                drivetrains,
                drivetrain,
            )

    return engine_positions, drivetrains


def _append_unique(
    values: list[str],
    value: str,
) -> None:
    if value not in values:
        values.append(value)