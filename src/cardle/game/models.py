from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class NamedEntity:
    id: str
    name: str


@dataclass(frozen=True)
class GameVehicle:
    id: str

    manufacturer: NamedEntity
    model: NamedEntity | None
    variant: NamedEntity
    version: NamedEntity | None

    production_start: int | None
    production_end: int | None
    power_hp: int | None

    vehicle_classes: frozenset[NamedEntity]
    body_styles: frozenset[NamedEntity]
    engine_families: frozenset[NamedEntity]
    drivetrains: frozenset[NamedEntity]

    lineage_neighbor_ids: frozenset[str]

    @property
    def display_name(self) -> str:
        parts = [self.manufacturer.name]

        if self.model is not None:
            parts.append(self.model.name)

        parts.append(self.variant.name)

        if self.version is not None:
            parts.append(self.version.name)

        return " ".join(parts)




class Closeness(str, Enum):
    MATCH = "match"
    VERY_CLOSE = "very_close"
    CLOSE = "close"
    RELATED = "related"
    FAR = "far"
    COLD = "cold"


class ColorFeedback(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    BLACK = "black"
    UNKNOWN = "unknown"


class OrderedFeedback(str, Enum):
    GREEN = "green"
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class GuessFeedback:
    closeness: Closeness

    manufacturer: ColorFeedback

    production_start: OrderedFeedback
    production_end: OrderedFeedback

    vehicle_class: ColorFeedback
    body_style: ColorFeedback
    engine_family: ColorFeedback

    power: OrderedFeedback

    drivetrain: ColorFeedback