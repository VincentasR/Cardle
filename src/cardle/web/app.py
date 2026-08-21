import os

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request
from neo4j import GraphDatabase

from ..game.comparison import VehicleComparer
from ..game.repository import Neo4jVehicleRepository
from ..game.session import GameSession
from ..game.target_selection import DailyTargetSelector

from .schemas import (
    GameStateRequest,
    GameStateResponse,
    VehicleSearchResponse,
)

from .serialization import serialize_game_state


# ============================================================
# Configuration
# ============================================================

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://127.0.0.1:7687",
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME",
    "neo4j",
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
)

NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "fullbmw",
)

if NEO4J_PASSWORD is None:
    raise RuntimeError(
        "NEO4J_PASSWORD environment variable is not set."
    )


# ============================================================
# Application lifecycle
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        ),
    )

    driver.verify_connectivity()

    repository = Neo4jVehicleRepository(
        driver=driver,
        database=NEO4J_DATABASE,
    )

    app.state.driver = driver
    app.state.repository = repository

    try:
        yield
    finally:
        driver.close()


app = FastAPI(
    title="Cardle API",
    lifespan=lifespan,
)


# ============================================================
# Routes
# ============================================================

@app.get("/api/hello")
def hello():
    return {
        "message": "Hello from Cardle",
    }


@app.get("/api/vehicles/search")
def search_vehicles(
    q: str,
    request: Request,
) -> list[VehicleSearchResponse]:
    repository = request.app.state.repository

    results = repository.search_vehicles(
        q,
        limit=20,
    )

    return [
        VehicleSearchResponse(
            id=vehicle.id,
            display_name=vehicle.display_name,
        )
        for vehicle in results
    ]


@app.post("/api/game/today/state")
def game_state(
    body: GameStateRequest,
    request: Request,
) -> GameStateResponse:
    repository = request.app.state.repository

    today = date.today()

    vehicles = repository.list_guessable_vehicles()

    if not vehicles:
        raise RuntimeError(
            "No guessable vehicles were found."
        )

    selector = DailyTargetSelector()

    selected = selector.select(
        vehicles=vehicles,
        day=today,
    )

    target = repository.get_vehicle(
        selected.id
    )

    game = GameSession(
        target=target,
        comparer=VehicleComparer(),
    )

    for vehicle_id in body.guess_ids:
        guess = repository.get_vehicle(
            vehicle_id
        )

        game.submit_guess(guess)

    return serialize_game_state(
        game=game,
        day=today,
    )