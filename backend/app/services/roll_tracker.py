import json
import os
from datetime import datetime, timezone
from pathlib import Path

_D_CORE_MM = 12  # typical thermal receipt roll core diameter (mm)
_BYTES_PER_MM2 = 14  # calibration: approx bytes per mm² of roll cross-section


class RollTracker:
    _DEFAULT = {
        "bytes_printed": 0,
        "roll_width_mm": 57,
        "roll_diameter_mm": 40,
        "last_reset": None,
        "hardware_paper_sensor_available": None,
    }

    def __init__(self):
        self._path: Path | None = None
        self._state: dict = {}

    @classmethod
    def load(cls, path) -> "RollTracker":
        tracker = cls()
        tracker._path = Path(path)
        if tracker._path.exists():
            tracker._state = json.loads(tracker._path.read_text())
        else:
            tracker._state = dict(cls._DEFAULT)
            tracker._state["last_reset"] = datetime.now(timezone.utc).isoformat()
            tracker.save()
        return tracker

    def save(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, indent=2))
        os.replace(tmp, self._path)  # atomic on POSIX; best-effort on Windows

    def add_bytes(self, n: int) -> None:
        self._state["bytes_printed"] = self._state.get("bytes_printed", 0) + n
        self.save()

    def reset(self, width_mm: int, diameter_mm: int) -> None:
        self._state["bytes_printed"] = 0
        self._state["roll_width_mm"] = width_mm
        self._state["roll_diameter_mm"] = diameter_mm
        self._state["last_reset"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def estimate_remaining(self) -> int:
        d = self._state.get("roll_diameter_mm", 40)
        area = (d / 2) ** 2 - (_D_CORE_MM / 2) ** 2
        total_bytes = max(1, area * _BYTES_PER_MM2)
        used_pct = int(self._state.get("bytes_printed", 0) / total_bytes * 100)
        return max(0, 100 - used_pct)

    @property
    def state(self) -> dict:
        return dict(self._state)
