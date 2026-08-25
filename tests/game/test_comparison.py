from src.cardle.game.comparison import VehicleComparer
from src.cardle.game.models import (
    Closeness,
    ColorFeedback,
    GameVehicle,
    NamedEntity,
    OrderedFeedback,
)


def test_exact_vehicle_is_all_green():
    vehicle = GameVehicle(
        id="test_vehicle",

        manufacturer=NamedEntity(
            id="bmw",
            name="BMW",
        ),

        model=None,

        variant=NamedEntity(
            id="test_variant",
            name="Test Variant",
        ),

        version=None,

        production_start=None,
        production_end=None,
        power_hp=None,

        vehicle_classes=frozenset(),
        body_styles=frozenset(),

        engine_series=frozenset(),
        engine_families=frozenset(),
        engines=frozenset(),

        drivetrains=frozenset(),

        lineage_neighbor_ids=frozenset(),
    )

    feedback = VehicleComparer().compare(
        vehicle,
        vehicle,
    )

    assert feedback.closeness == Closeness.MATCH
    assert feedback.manufacturer == ColorFeedback.GREEN
    assert feedback.production_start == OrderedFeedback.GREEN
    assert feedback.production_end == OrderedFeedback.GREEN
    assert feedback.vehicle_class == ColorFeedback.GREEN
    assert feedback.body_style == ColorFeedback.GREEN
    assert feedback.engine_family == ColorFeedback.GREEN
    assert feedback.power == OrderedFeedback.GREEN
    assert feedback.drivetrain == ColorFeedback.GREEN