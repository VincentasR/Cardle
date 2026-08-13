def parse_layout(value: str) -> tuple[list[str], list[str]]:
    value_lower = value.lower()

    engine_positions = []
    drivetrains = []

    # Engine position
    if "front-engine" in value_lower:
        engine_positions.append("Front")

    if "mid-engine" in value_lower:
        engine_positions.append("Mid")

    if "rear-engine" in value_lower:
        engine_positions.append("Rear")

    # Drivetrain
    if "front-wheel-drive" in value_lower:
        drivetrains.append("FWD")

    if "rear-wheel-drive" in value_lower:
        drivetrains.append("RWD")

    if (
        "all-wheel-drive" in value_lower
        or "four-wheel-drive" in value_lower
        or "4-wheel-drive" in value_lower
        or "xdrive" in value_lower
    ):
        drivetrains.append("AWD")

    # Abbreviated layouts
    abbreviations = {
        "fr": ("Front", "RWD"),
        "ff": ("Front", "FWD"),
        "mr": ("Mid", "RWD"),
        "rr": ("Rear", "RWD"),
        "f4": ("Front", "AWD"),
        "m4": ("Mid", "AWD"),
        "r4": ("Rear", "AWD"),
    }

    stripped = value_lower.strip()

    for abbreviation, (position, drivetrain) in abbreviations.items():
        if stripped.startswith(abbreviation):
            if position not in engine_positions:
                engine_positions.append(position)

            if drivetrain not in drivetrains:
                drivetrains.append(drivetrain)

            break

    return engine_positions, drivetrains