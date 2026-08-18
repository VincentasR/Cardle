import os

from neo4j import GraphDatabase

from .comparison import VehicleComparer
from .repository import Neo4jVehicleRepository
from .session import GameSession


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

        guess = repository.get_vehicle(
            "bmw_3_series_e36_325i"
        )

        game = GameSession(
            target=target,
            comparer=comparer,
        )

        result = game.submit_guess(guess)

        print(result)
        print(f"Guesses: {game.guess_count}")
        print(f"Won: {game.won}")

        result = game.submit_guess(target)

        print()
        print(result)
        print(f"Guesses: {game.guess_count}")
        print(f"Won: {game.won}")


if __name__ == "__main__":
    main()