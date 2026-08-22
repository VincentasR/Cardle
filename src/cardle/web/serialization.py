from datetime import date

from ..game.session import GameSession, GuessResult
from .schemas import (
    GameStateResponse,
    GuessFeedbackResponse,
    GuessResultResponse,
    GuessVehicleResponse,
    TargetVehicleResponse,
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
            TargetVehicleResponse(
                id=game.target.id,
                display_name=game.target.display_name,
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

        vehicle=GuessVehicleResponse(
            id=guess.id,
            display_name=guess.display_name,
            manufacturer=guess.manufacturer.name,

            production_start=guess.production_start,
            production_end=guess.production_end,

            vehicle_classes=sorted(
                entity.name
                for entity in guess.vehicle_classes
            ),

            body_styles=sorted(
                entity.name
                for entity in guess.body_styles
            ),

            engine_series=sorted(
                entity.name for entity in guess.engine_series
            ),
            engine_families=sorted(
                entity.name for entity in guess.engine_families
            ),
            engines=sorted(
                entity.name for entity in guess.engines
            ),

            power_hp=guess.power_hp,

            drivetrains=sorted(
                entity.name
                for entity in guess.drivetrains
            ),
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