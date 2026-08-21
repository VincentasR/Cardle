from datetime import date

from .models import VehicleOption
from .target_selection import DailyTargetSelector


def main():
    vehicles = [
        VehicleOption(
            id="car_a",
            display_name="Car A",
        ),
        VehicleOption(
            id="car_b",
            display_name="Car B",
        ),
        VehicleOption(
            id="car_c",
            display_name="Car C",
        ),
        VehicleOption(
            id="car_d",
            display_name="Car D",
        ),
    ]

    selector = DailyTargetSelector()

    day_1 = date(2026, 8, 18)
    day_2 = date(2026, 8, 19)

    first = selector.select(
        vehicles,
        day_1,
    )

    second = selector.select(
        vehicles,
        day_1,
    )

    tomorrow = selector.select(
        vehicles,
        day_2,
    )

    print("First:")
    print(first)

    print()
    print("Same day again:")
    print(second)

    print()
    print("Tomorrow:")
    print(tomorrow)

    assert first == second


if __name__ == "__main__":
    main()