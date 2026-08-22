import argparse
import os
from datetime import date

from neo4j import GraphDatabase

from .comparison import VehicleComparer
from .models import (
    GameVehicle,
    GuessFeedback,
    NamedEntity,
)
from .repository import Neo4jVehicleRepository
from .session import GameSession
from .session_store import FileSessionStore
from .target_selection import DailyTargetSelector


def main():
    args = _parse_args()

    uri = os.getenv(
        "NEO4J_URI",
        "bolt://127.0.0.1:7687",
    )

    username = os.getenv(
        "NEO4J_USERNAME",
        "neo4j",
    )

    password = os.getenv(
        "NEO4J_PASSWORD"
    )

    database = os.getenv(
        "NEO4J_DATABASE",
        "fullbmw",
    )

    if password is None:
        raise SystemExit(
            "NEO4J_PASSWORD environment variable is not set."
        )

    today = date.today()

    with GraphDatabase.driver(
        uri,
        auth=(username, password),
    ) as driver:

        repository = Neo4jVehicleRepository(
            driver=driver,
            database=database,
        )

        comparer = VehicleComparer()

        target = _choose_target(
            repository=repository,
            target_id=args.target,
            day=today,
        )

        game = GameSession(
            target=target,
            comparer=comparer,
        )

        store = None

        if args.target is None:
            store = FileSessionStore()

            saved = store.load(today)

            if saved is not None:
                for vehicle_id in saved.guessed_vehicle_ids:
                    guess = repository.get_vehicle(
                        vehicle_id
                    )

                    game.submit_guess(
                        guess
                    )

        _run_game(
            repository=repository,
            game=game,
            store=store,
            day=today,
        )


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Play Cardle."
    )

    parser.add_argument(
        "--target",
        default=None,
        help=(
            "Canonical vehicle ID to use as the target. "
            "If omitted, today's deterministic target "
            "is selected."
        ),
    )

    return parser.parse_args()


def _choose_target(
    repository: Neo4jVehicleRepository,
    target_id: str | None,
    day: date,
) -> GameVehicle:

    if target_id is not None:
        return repository.get_vehicle(
            target_id
        )

    vehicles = repository.list_guessable_vehicles()

    if not vehicles:
        raise RuntimeError(
            "No guessable vehicles were found."
        )

    selector = DailyTargetSelector()

    selected = selector.select(
        vehicles=vehicles,
        day=day,
    )

    return repository.get_vehicle(
        selected.id
    )


def _run_game(
    repository: Neo4jVehicleRepository,
    game: GameSession,
    store: FileSessionStore | None,
    day: date,
):
    print()
    print("==============================")
    print("           CARDLE")
    print("==============================")
    print()
    print("Guess the hidden car.")
    print("Type 'quit' to exit.")
    print()

    _print_guess_history(
        game
    )

    if game.won:
        print("==============================")
        print("Today's Cardle is complete!")
        print(
            f"The car was: {game.target.display_name}"
        )
        print(
            f"Guesses: {game.guess_count}"
        )
        print("==============================")
        return

    while not game.won:
        print(
            f"--- Guess {game.guess_count + 1} ---"
        )

        guess = _choose_vehicle(
            repository=repository,
            game=game,
        )

        if guess is None:
            print()

            if store is not None:
                print("Progress saved.")
                print(
                    "Come back later to continue "
                    "today's Cardle."
                )
            else:
                print("Game ended.")

            return

        result = game.submit_guess(
            guess
        )

        if store is not None:
            store.save(
                day=day,
                guessed_vehicle_ids=[
                    result.guess.id
                    for result in game.guesses
                ],
            )

        print()

        _print_feedback(
            guess=result.guess,
            feedback=result.feedback,
        )

        print()

    print("==============================")
    print("Correct!")
    print(
        f"The car was: {game.target.display_name}"
    )
    print(
        f"Guesses: {game.guess_count}"
    )
    print("==============================")


def _choose_vehicle(
    repository: Neo4jVehicleRepository,
    game: GameSession,
) -> GameVehicle | None:

    while True:
        search_text = input(
            "Search car: "
        ).strip()

        if search_text.lower() in {
            "quit",
            "exit",
            "q",
        }:
            return None

        results = repository.search_vehicles(
            search_text,
            limit=20,
        )

        if not results:
            print("No cars found.")
            print()
            continue

        print()

        for index, vehicle in enumerate(
            results,
            start=1,
        ):
            already_guessed = (
                " [guessed]"
                if game.has_guessed(vehicle.id)
                else ""
            )

            print(
                f"{index}. "
                f"{vehicle.display_name}"
                f"{already_guessed}"
            )

        print()

        selection = input(
            "Choose a car number "
            "(or press Enter to search again): "
        ).strip()

        if not selection:
            print()
            continue

        try:
            index = int(selection)
        except ValueError:
            print("Please enter a number.")
            print()
            continue

        if index < 1 or index > len(results):
            print("Invalid selection.")
            print()
            continue

        selected = results[index - 1]

        if game.has_guessed(
            selected.id
        ):
            print()
            print(
                f"You already guessed "
                f"{selected.display_name}."
            )
            print()
            continue

        return repository.get_vehicle(
            selected.id
        )


def _print_guess_history(
    game: GameSession,
) -> None:

    if not game.guesses:
        return

    print("Resuming today's game.")
    print()

    for result in game.guesses:
        print(
            f"--- Guess {result.guess_number} ---"
        )

        _print_feedback(
            guess=result.guess,
            feedback=result.feedback,
        )

        print()


def _print_feedback(
    guess: GameVehicle,
    feedback: GuessFeedback,
):
    print(
        guess.display_name
    )

    print()

    print(
        "Car closeness:  "
        f"{feedback.closeness.value}"
    )

    print(
        "Manufacturer:   "
        f"{guess.manufacturer.name} "
        f"[{feedback.manufacturer.value}]"
    )

    print(
        "Production:     "
        f"{_display_value(guess.production_start)} "
        f"[{feedback.production_start.value}]"
        " — "
        f"{_display_value(guess.production_end)} "
        f"[{feedback.production_end.value}]"
    )

    print(
        "Vehicle class:  "
        f"{_display_entities(guess.vehicle_classes)} "
        f"[{feedback.vehicle_class.value}]"
    )

    print(
        "Body style:     "
        f"{_display_entities(guess.body_styles)} "
        f"[{feedback.body_style.value}]"
    )

    print(
        "Engine:         "
        f"{_display_entities(guess.display_engines)} "
        f"[{feedback.engine_family.value}]"
    )

    power = (
        f"{guess.power_hp} hp"
        if guess.power_hp is not None
        else "Unknown"
    )

    print(
        "Power:          "
        f"{power} "
        f"[{feedback.power.value}]"
    )

    print(
        "Drivetrain:     "
        f"{_display_entities(guess.drivetrains)} "
        f"[{feedback.drivetrain.value}]"
    )


def _display_entities(
    entities: frozenset[NamedEntity],
) -> str:

    if not entities:
        return "Unknown"

    return ", ".join(
        sorted(
            entity.name
            for entity in entities
        )
    )


def _display_value(
    value: int | None,
) -> str:

    if value is None:
        return "Unknown"

    return str(value)


if __name__ == "__main__":
    main()