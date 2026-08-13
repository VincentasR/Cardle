import re


BODY_STYLE_ALIASES = {
    "coupe": "Coupe",
    "coupé": "Coupe",
    "sedan": "Sedan",
    "saloon": "Sedan",
    "wagon": "Wagon",
    "estate": "Wagon",
    "touring": "Wagon",
    "hatchback": "Hatchback",
    "convertible": "Convertible",
    "cabriolet": "Convertible",
    "roadster": "Roadster",
    "suv": "SUV",
    "pickup": "Pickup",
    "pick-up": "Pickup",
}


def parse_body_styles(value: str) -> list[str]:
    value_lower = value.lower()

    found = []

    for alias, canonical in BODY_STYLE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", value_lower):
            if canonical not in found:
                found.append(canonical)

    return found