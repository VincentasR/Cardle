from dataclasses import dataclass

from .comparison import VehicleComparer
from .models import (
    GameVehicle,
    GuessFeedback,
)


@dataclass(frozen=True)
class GuessResult:
    guess: GameVehicle
    feedback: GuessFeedback
    guess_number: int


class GameSession:
    def __init__(
        self,
        target: GameVehicle,
        comparer: VehicleComparer,
    ):
        self._target = target
        self._comparer = comparer

        self._guesses: list[GuessResult] = []
        self._guessed_vehicle_ids: set[str] = set()

        self._won = False

    @property
    def target(self) -> GameVehicle:
        return self._target

    @property
    def guesses(self) -> tuple[GuessResult, ...]:
        return tuple(self._guesses)

    @property
    def guess_count(self) -> int:
        return len(self._guesses)

    @property
    def won(self) -> bool:
        return self._won

    def has_guessed(
        self,
        vehicle_id: str,
    ) -> bool:
        return vehicle_id in self._guessed_vehicle_ids

    def submit_guess(
        self,
        guess: GameVehicle,
    ) -> GuessResult:
        if self._won:
            raise RuntimeError(
                "The game has already been won."
            )

        if self.has_guessed(guess.id):
            raise ValueError(
                f"{guess.display_name} has already been guessed."
            )

        feedback = self._comparer.compare(
            guess,
            self._target,
        )

        result = GuessResult(
            guess=guess,
            feedback=feedback,
            guess_number=self.guess_count + 1,
        )

        self._guesses.append(result)
        self._guessed_vehicle_ids.add(guess.id)

        if guess.id == self._target.id:
            self._won = True

        return result