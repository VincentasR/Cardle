import re


def parse_power_hp(value: str) -> int | None:
    """
    Extract horsepower from a raw Wikipedia power string.

    Examples:
        "136 kW (185 PS; 182 hp) at 5,800 rpm"
        -> 182

        "191 kW (256 hp) at 6,500 rpm"
        -> 256
    """
    match = re.search(
        r"(\d+)\s*(?:hp|bhp)\b",
        value,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return int(match.group(1))