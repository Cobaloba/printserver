import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_D_CORE_MM = 12      # typical thermal receipt roll core diameter (mm)
_BYTES_PER_MM2 = 14  # fallback calibration: approx bytes per mm² of roll cross-section
_NEAR_END_FRACTION = 0.15  # hardware sensor fires when ~15% paper remains


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
            try:
                loaded = json.loads(tracker._path.read_text())
                tracker._state = {**cls._DEFAULT, **loaded}
            except (json.JSONDecodeError, ValueError):
                logger.warning("Roll state file corrupt, resetting to defaults")
                tracker._state = dict(cls._DEFAULT)
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
        self._state["calibrated_bytes_per_mm2"] = None  # fresh roll, fresh calibration
        self.save()

    def calibrate_from_near_end(self, bytes_at_near_end: int) -> None:
        """Self-calibrate when hardware sensor reports paper_near_end.

        When the sensor fires, ~NEAR_END_FRACTION of paper remains, so the bytes
        printed so far represent (1 - NEAR_END_FRACTION) of the total. Back-calculate
        the real bytes_per_mm2 for this roll and persist it.
        Only runs once per roll — subsequent near-end signals are ignored.
        """
        if self._state.get("calibrated_bytes_per_mm2") is not None:
            return  # already calibrated for this roll
        d = self._state.get("roll_diameter_mm", 40)
        area = (d / 2) ** 2 - (_D_CORE_MM / 2) ** 2
        if area <= 0 or bytes_at_near_end <= 0:
            return
        estimated_total = bytes_at_near_end / (1 - _NEAR_END_FRACTION)
        calibrated = estimated_total / area
        self._state["calibrated_bytes_per_mm2"] = calibrated
        logger.info(
            "Roll self-calibrated: %.1f bytes/mm² (default was %d) from %d bytes at near-end",
            calibrated, _BYTES_PER_MM2, bytes_at_near_end,
        )
        self.save()

    def estimate_remaining(self) -> int:
        d = self._state.get("roll_diameter_mm", 40)
        area = (d / 2) ** 2 - (_D_CORE_MM / 2) ** 2
        cal = self._state.get("calibrated_bytes_per_mm2") or _BYTES_PER_MM2
        total_bytes = max(1, area * cal)
        used_pct = int(self._state.get("bytes_printed", 0) / total_bytes * 100)
        return max(0, 100 - used_pct)

    @property
    def state(self) -> dict:
        return dict(self._state)
