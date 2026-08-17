import os

from neo4j import GraphDatabase

from .comparison import VehicleComparer
from .repository import Neo4jVehicleRepository


def main():
    uri = os.getenv(
        "NEO4J_URI",
        "bolt://127.0.0.1:7687",
    )
    username = os.getenv(
        "NEO4J_USERNAME",
        "neo4j",
    )
    password = os.environ["NEO4J_PASSWORD"]
    database = os.getenv(
        "NEO4J_DATABASE",
        "fullbmw",
    )

    with GraphDatabase.driver(
        uri,
        auth=(username, password),
    ) as driver:
        repository = Neo4jVehicleRepository(
            driver=driver,
            database=database,
        )

        comparer = VehicleComparer()

        target = repository.get_vehicle(
            "bmw_6_series_e24_635csi"
        )

        # Put the REAL E24 version ID you used earlier here.
        guess = repository.get_vehicle(
            "bmw_6_series_e63_630i"
        )

        feedback = comparer.compare(
            guess,
            target,
        )

        print("TARGET")
        print(target.display_name)

        print()
        print("GUESS")
        print(guess.display_name)

        print()
        print("FEEDBACK")
        print(f"Closeness:        {feedback.closeness.value}")
        print(f"Manufacturer:     {feedback.manufacturer.value}")
        print(
            f"Production start: {feedback.production_start.value}"
        )
        print(
            f"Production end:   {feedback.production_end.value}"
        )
        print(
            f"Vehicle class:    {feedback.vehicle_class.value}"
        )
        print(f"Body style:       {feedback.body_style.value}")
        print(
            f"Engine family:    {feedback.engine_family.value}"
        )
        print(f"Power:            {feedback.power.value}")
        print(f"Drivetrain:       {feedback.drivetrain.value}")


if __name__ == "__main__":
    main()