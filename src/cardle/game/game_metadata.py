from dataclasses import dataclass


@dataclass(frozen=True)
class ManufacturerOrigin:
    country: str
    continent: str


MANUFACTURER_ORIGINS = {
    "bmw": ManufacturerOrigin(
        country="Germany",
        continent="Europe",
    ),

    # Add manufacturers here as they enter the dataset.
    #
    # "ferrari": ManufacturerOrigin(
    #     country="Italy",
    #     continent="Europe",
    # ),
    #
    # "lamborghini": ManufacturerOrigin(
    #     country="Italy",
    #     continent="Europe",
    # ),
    #
    # "toyota": ManufacturerOrigin(
    #     country="Japan",
    #     continent="Asia",
    # ),
}


# ---------------------------------------------------------
# Vehicle-class similarity
#
# Exact matches are handled separately by VehicleComparer.
#
# Yellow = closely related.
# Orange = broadly related.
#
# frozenset makes every relationship symmetric:
#
#   A ↔ B
#
# rather than having to define A → B and B → A.
# ---------------------------------------------------------

VEHICLE_CLASS_YELLOW_PAIRS = {
    # Luxury crossover SUVs
    frozenset({
        "Subcompact luxury crossover SUV",
        "Compact luxury crossover SUV",
    }),
    frozenset({
        "Compact luxury crossover SUV",
        "Mid-size luxury crossover SUV",
    }),

    # General passenger cars
    frozenset({
        "City car",
        "Small family car",
    }),
    frozenset({
        "Small family car",
        "Mid-size car",
    }),

    # Similar size, different premium positioning
    frozenset({
        "Small family car",
        "Subcompact executive car",
    }),
    frozenset({
        "Mid-size car",
        "Compact executive car",
    }),

    # Executive / luxury progression
    frozenset({
        "Subcompact executive car",
        "Compact executive car",
    }),
    frozenset({
        "Compact executive car",
        "Executive car",
    }),
    frozenset({
        "Executive car",
        "Full-size luxury car",
    }),
    frozenset({
        "Executive car",
        "Luxury car",
    }),
    frozenset({
        "Full-size luxury car",
        "Luxury car",
    }),

    # Sporting cars
    frozenset({
        "Sports car",
        "Roadster",
    }),
    frozenset({
        "Sports car",
        "Grand tourer",
    }),
}


VEHICLE_CLASS_ORANGE_PAIRS = {
    # Wider SUV size difference
    frozenset({
        "Subcompact luxury crossover SUV",
        "Mid-size luxury crossover SUV",
    }),

    # Broader passenger-car relationships
    frozenset({
        "City car",
        "Subcompact executive car",
    }),
    frozenset({
        "Small family car",
        "Compact executive car",
    }),
    frozenset({
        "Mid-size car",
        "Executive car",
    }),

    # Executive hierarchy with one or more levels skipped
    frozenset({
        "Subcompact executive car",
        "Executive car",
    }),
    frozenset({
        "Compact executive car",
        "Full-size luxury car",
    }),
    frozenset({
        "Compact executive car",
        "Luxury car",
    }),

    # GTs overlap somewhat with large luxury/executive cars
    frozenset({
        "Grand tourer",
        "Executive car",
    }),
    frozenset({
        "Grand tourer",
        "Luxury car",
    }),
    frozenset({
        "Grand tourer",
        "Full-size luxury car",
    }),

    # Both open/sporting cars, but less directly related
    # than Roadster ↔ Sports car.
    frozenset({
        "Roadster",
        "Grand tourer",
    }),
}