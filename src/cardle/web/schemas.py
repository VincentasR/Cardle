from pydantic import BaseModel

from ..game.models import (
    Closeness,
    ColorFeedback,
    OrderedFeedback,
)


class GameStateRequest(BaseModel):
    guess_ids: list[str]


class VehicleSearchResponse(BaseModel):
    id: str
    display_name: str


class TargetVehicleResponse(BaseModel):
    id: str
    display_name: str


class GuessVehicleResponse(BaseModel):
    id: str
    display_name: str

    manufacturer: str

    production_start: int | None
    production_end: int | None

    vehicle_classes: list[str]
    body_styles: list[str]

    engine_series: list[str]
    engine_families: list[str]
    engines: list[str]

    power_hp: int | None

    drivetrains: list[str]


class GuessFeedbackResponse(BaseModel):
    closeness: Closeness

    manufacturer: ColorFeedback

    production_start: OrderedFeedback
    production_end: OrderedFeedback

    vehicle_class: ColorFeedback
    body_style: ColorFeedback
    engine_family: ColorFeedback

    power: OrderedFeedback

    drivetrain: ColorFeedback


class GuessResultResponse(BaseModel):
    guess_number: int

    vehicle: GuessVehicleResponse
    feedback: GuessFeedbackResponse


class GameStateResponse(BaseModel):
    date: str

    won: bool
    lost: bool
    finished: bool

    guess_count: int
    max_guesses: int
    remaining_guesses: int

    target: TargetVehicleResponse | None

    guesses: list[GuessResultResponse]

# ============================================================
# Automotive Universe
# ============================================================

from typing import Literal


UniverseNodeType = Literal[
    "manufacturer",
    "model",
    "variant",
    "version",
    "engine_family",
]

UniverseEdgeType = Literal[
    "hierarchy",
    "version",
    "engine",
]


class UniverseGraphRequest(BaseModel):
    unlocked_vehicle_ids: list[str]


class UniverseNodeResponse(BaseModel):
    id: str
    entity_id: str
    label: str
    type: UniverseNodeType

    manufacturer_id: str | None = None
    parent_model_id: str | None = None
    parent_variant_id: str | None = None

    production_start: int | None = None
    production_end: int | None = None

    vehicle_classes: list[str] = []
    body_styles: list[str] = []
    drivetrains: list[str] = []

    power_hp: int | None = None
    engine_labels: list[str] = []


class UniverseEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    type: UniverseEdgeType


class UniverseGraphResponse(BaseModel):
    nodes: list[UniverseNodeResponse]
    edges: list[UniverseEdgeResponse]

