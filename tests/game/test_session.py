import pytest

from src.cardle.game.comparison import VehicleComparer
from src.cardle.game.models import GameVehicle, NamedEntity
from src.cardle.game.session import GameSession


def make_vehicle(
    vehicle_id: str,
    name: str,
) -> GameVehicle:
    return GameVehicle(
        id=vehicle_id,

        manufacturer=NamedEntity(
            id="bmw",
            name="BMW",
        ),

        model=NamedEntity(
            id="3_series",
            name="3 Series",
        ),

        variant=NamedEntity(
            id=f"{vehicle_id}_variant",
            name=f"{name} Variant",
        ),

        version=NamedEntity(
            id=vehicle_id,
            name=name,
        ),

        production_start=2000,
        production_end=2005,
        power_hp=150,

        vehicle_classes=frozenset(),
        body_styles=frozenset(),
        engine_families=frozenset(),
        drivetrains=frozenset(),

        lineage_neighbor_ids=frozenset(),
    )


def make_game() -> tuple[GameSession, GameVehicle]:
    target = make_vehicle(
        "target",
        "Target",
    )

    game = GameSession(
        target=target,
        comparer=VehicleComparer(),
    )

    return game, target


def test_seven_wrong_guesses_lose_game():
    game, _ = make_game()

    for number in range(7):
        guess = make_vehicle(
            f"wrong_{number}",
            f"Wrong {number}",
        )

        game.submit_guess(guess)

    assert game.guess_count == 7
    assert game.remaining_guesses == 0

    assert game.lost
    assert not game.won
    assert game.finished


def test_correct_seventh_guess_wins_game():
    game, target = make_game()

    for number in range(6):
        guess = make_vehicle(
            f"wrong_{number}",
            f"Wrong {number}",
        )

        game.submit_guess(guess)

    game.submit_guess(target)

    assert game.guess_count == 7
    assert game.remaining_guesses == 0

    assert game.won
    assert not game.lost
    assert game.finished


def test_duplicate_guess_is_rejected():
    game, _ = make_game()

    guess = make_vehicle(
        "duplicate",
        "Duplicate",
    )

    game.submit_guess(guess)

    with pytest.raises(ValueError):
        game.submit_guess(guess)

    assert game.guess_count == 1


def test_guess_after_finished_game_is_rejected():
    game, _ = make_game()

    for number in range(7):
        game.submit_guess(
            make_vehicle(
                f"wrong_{number}",
                f"Wrong {number}",
            )
        )

    with pytest.raises(RuntimeError):
        game.submit_guess(
            make_vehicle(
                "guess_8",
                "Guess 8",
            )
        )

    assert game.guess_count == 7