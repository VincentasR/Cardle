import re


VEHICLE_CLASS_ALIASES = {
    "grand tourer": "Grand tourer",
    "sports car": "Sports car",
    "executive car": "Executive car",
    "compact executive car": "Compact executive car",
    "subcompact executive car": "Subcompact executive car",
    "full-size luxury car": "Full-size luxury car",
    "mid-size luxury crossover suv": "Mid-size luxury crossover SUV",
    "compact luxury crossover suv": "Compact luxury crossover SUV",
    "subcompact luxury crossover suv": "Subcompact luxury crossover SUV",
    "small family car": "Small family car",
    "mid-size car": "Mid-size car",
    "city car": "City car",
    "luxury car": "Luxury car",
    "roadster": "Roadster",
}


def parse_vehicle_classes(value: str) -> list[str]:
    value_lower = value.lower()

    found = []

    for alias, canonical in VEHICLE_CLASS_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", value_lower):
            if canonical not in found:
                found.append(canonical)

    return found