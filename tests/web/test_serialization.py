from datetime import date

from src.cardle.game.comparison import VehicleComparer
from src.cardle.game.models import GameVehicle, NamedEntity
from src.cardle.game.session import GameSession
from src.cardle.web.serialization import serialize_game_state


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


def test_target_is_hidden_while_game_is_active():
    target = make_vehicle(
        "secret_target",
        "Secret Target",
    )

    game = GameSession(
        target=target,
        comparer=VehicleComparer(),
    )

    response = serialize_game_state(
        game=game,
        day=date(2026, 8, 21),
    )

    assert not response.finished
    assert response.target is None


def test_target_is_revealed_after_game_finishes():
    target = make_vehicle(
        "secret_target",
        "Secret Target",
    )

    game = GameSession(
        target=target,
        comparer=VehicleComparer(),
    )

    game.submit_guess(target)

    response = serialize_game_state(
        game=game,
        day=date(2026, 8, 21),
    )

    assert response.finished
    assert response.target is not None

    assert response.target.id == target.id
    assert (
        response.target.display_name
        == target.display_name
    )