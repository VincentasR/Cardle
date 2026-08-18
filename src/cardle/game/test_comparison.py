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

        # -----------------------------------------
        # Test list_guessable_vehicles()
        # -----------------------------------------

        vehicles = repository.list_guessable_vehicles()

        print(f"Guessable vehicles: {len(vehicles)}")
        print()

        for vehicle in vehicles[:30]:
            print(
                vehicle.id,
                "->",
                vehicle.display_name,
            )

        # -----------------------------------------
        # Existing comparison test
        # -----------------------------------------
        results = [repository.search_vehicles(i) for i in ["635", "x5", "e34", "e46"]]
        for i in results:


            print("SEARCH RESULTS")
            print()

            for index, vehicle in enumerate(
                i,
                start=1,
            ):
                print(
                    f"{index}. {vehicle.display_name}"
                )
            comparer = VehicleComparer()

        target = repository.get_vehicle(
            "bmw_6_series_e24_635csi"
        )

        guess = repository.get_vehicle(
            "bmw_6_series_e24_635csi"
        )

        feedback = comparer.compare(
            guess,
            target,
        )

        print()
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