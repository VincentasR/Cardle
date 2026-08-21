import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class SavedSession:
    day: date
    guessed_vehicle_ids: tuple[str, ...]


class FileSessionStore:
    def __init__(
        self,
        path: Path | None = None,
    ):
        if path is None:
            path = (
                Path.home()
                / ".cardle"
                / "session.json"
            )

        self._path = path

    def load(
        self,
        day: date,
    ) -> SavedSession | None:
        if not self._path.exists():
            return None

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        saved_day = date.fromisoformat(
            data["date"]
        )

        # Previous day's game does not belong
        # to today's session.
        if saved_day != day:
            return None

        return SavedSession(
            day=saved_day,
            guessed_vehicle_ids=tuple(
                data.get("guesses", [])
            ),
        )

    def save(
        self,
        day: date,
        guessed_vehicle_ids: list[str],
    ) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "date": day.isoformat(),
            "guesses": guessed_vehicle_ids,
        }

        with self._path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
            )