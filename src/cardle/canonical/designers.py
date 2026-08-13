import re


def parse_designers(value: str) -> list[str]:
    """
    Parse a raw designer string into individual designer names.

    Example:
        "Paul Bracq" -> ["Paul Bracq"]
    """
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = re.sub(r"\([^)]*\)", "", value)

    parts = re.split(r",|\band\b", value)

    designers = []

    for part in parts:
        name = part.strip()

        if name and name not in designers:
            designers.append(name)

    return designers