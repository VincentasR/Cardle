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
    engine_families: list[str]

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