from datetime import date
import hashlib

from .models import VehicleOption


class DailyTargetSelector:
    def __init__(
        self,
        seed: str = "cardle-v1",
    ):
        self._seed = seed

    def select(
        self,
        vehicles: list[VehicleOption],
        day: date | None = None,
    ) -> VehicleOption:
        if not vehicles:
            raise ValueError(
                "Cannot select a target from an empty vehicle list."
            )

        if day is None:
            day = date.today()

        # Never depend on whatever order Neo4j happened
        # to return the vehicles in.
        vehicles = sorted(
            vehicles,
            key=lambda vehicle: vehicle.id,
        )

        key = (
            f"{self._seed}:{day.isoformat()}"
        )

        digest = hashlib.sha256(
            key.encode("utf-8")
        ).digest()

        number = int.from_bytes(
            digest,
            byteorder="big",
        )

        index = number % len(vehicles)

        return vehicles[index]