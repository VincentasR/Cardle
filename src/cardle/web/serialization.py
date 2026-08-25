from datetime import date

from ..game.models import GameVehicle
from ..game.session import GameSession, GuessResult

from .schemas import (
    GameStateResponse,
    GuessFeedbackResponse,
    GuessResultResponse,
    GuessVehicleResponse,
)


def serialize_vehicle(
    vehicle: GameVehicle,
) -> GuessVehicleResponse:
    return GuessVehicleResponse(
        id=vehicle.id,
        display_name=vehicle.display_name,
        manufacturer=vehicle.manufacturer.name,

        production_start=vehicle.production_start,
        production_end=vehicle.production_end,

        vehicle_classes=sorted(
            entity.name
            for entity in vehicle.vehicle_classes
        ),

        body_styles=sorted(
            entity.name
            for entity in vehicle.body_styles
        ),

        engine_series=sorted(
            entity.name
            for entity in vehicle.engine_series
        ),

        engine_families=sorted(
            entity.name
            for entity in vehicle.engine_families
        ),

        engines=sorted(
            entity.name
            for entity in vehicle.engines
        ),

        power_hp=vehicle.power_hp,

        drivetrains=sorted(
            entity.name
            for entity in vehicle.drivetrains
        ),
    )


def serialize_game_state(
    game: GameSession,
    day: date,
) -> GameStateResponse:
    return GameStateResponse(
        date=day.isoformat(),

        won=game.won,
        lost=game.lost,
        finished=game.finished,

        guess_count=game.guess_count,
        max_guesses=game.max_guesses,
        remaining_guesses=game.remaining_guesses,

        target=(
            serialize_vehicle(
                game.target,
            )
            if game.finished
            else None
        ),

        guesses=[
            serialize_guess(result)
            for result in game.guesses
        ],
    )


def serialize_guess(
    result: GuessResult,
) -> GuessResultResponse:
    guess = result.guess
    feedback = result.feedback

    return GuessResultResponse(
        guess_number=result.guess_number,

        vehicle=serialize_vehicle(
            guess,
        ),

        feedback=GuessFeedbackResponse(
            closeness=feedback.closeness,
            manufacturer=feedback.manufacturer,

            production_start=feedback.production_start,
            production_end=feedback.production_end,

            vehicle_class=feedback.vehicle_class,
            body_style=feedback.body_style,
            engine_family=feedback.engine_family,

            power=feedback.power,

            drivetrain=feedback.drivetrain,
        ),
    )