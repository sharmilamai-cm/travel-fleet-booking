"""JSON file persistence with basic error handling."""

import json
import os
import tempfile

EMPTY_DB = {
    "vehicles": [],
    "routes": [],
    "trips": [],
    "bookings": [],
    "counters": {"vehicles": 0, "routes": 0, "trips": 0, "bookings": 0},
}


class StorageError(RuntimeError):
    """Raised when the data file cannot be read or written."""


class JsonStore:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return json.loads(json.dumps(EMPTY_DB))  # deep copy
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise StorageError(f"Data file {self.path} is corrupted: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Cannot read {self.path}: {exc}") from exc
        for key, default in EMPTY_DB.items():
            data.setdefault(key, json.loads(json.dumps(default)))
        return data

    def save(self, data: dict) -> None:
        folder = os.path.dirname(os.path.abspath(self.path))
        try:
            os.makedirs(folder, exist_ok=True)
            # write to a temp file first so a crash cannot corrupt the real file
            fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            os.replace(tmp_path, self.path)
        except OSError as exc:
            raise StorageError(f"Cannot write {self.path}: {exc}") from exc
