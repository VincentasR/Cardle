import os

from neo4j import GraphDatabase

from .repository import Neo4jVehicleRepository
from .comparison import VehicleComparer

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
        "neo4j",
    )

    with GraphDatabase.driver(
        uri,
        auth=(username, password),
    ) as driver:
        repository = Neo4jVehicleRepository(
            driver=driver,
            database=database,
        )

        vehicle = repository.get_vehicle(
            "bmw_6_series_e24_635csi"
        )

        print(vehicle)
        print()
        print(vehicle.display_name)
        target = repository.get_vehicle(
            "bmw_6_series_e24_635csi"
        )

        guess = repository.get_vehicle(
            "bmw_3_series_e36_325i"
        )

        comparer = VehicleComparer()

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
        print(feedback)

if __name__ == "__main__":
    main()