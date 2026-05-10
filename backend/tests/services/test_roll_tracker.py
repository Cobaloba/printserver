import json
import pytest
from app.services.roll_tracker import RollTracker


def test_load_creates_default_when_missing(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    assert tmp_roll_state.exists()
    state = json.loads(tmp_roll_state.read_text())
    assert state["bytes_printed"] == 0
    assert state["roll_width_mm"] == 57
    assert state["roll_diameter_mm"] == 40
    assert state["last_reset"] is not None
    assert state["hardware_paper_sensor_available"] is None


def test_load_reads_existing_file(tmp_roll_state):
    tmp_roll_state.write_text(json.dumps({
        "bytes_printed": 1234,
        "roll_width_mm": 57,
        "roll_diameter_mm": 40,
        "last_reset": "2026-01-01T00:00:00Z",
        "hardware_paper_sensor_available": None,
    }))
    tracker = RollTracker.load(tmp_roll_state)
    assert tracker.state["bytes_printed"] == 1234


def test_add_bytes_persists_to_disk(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(500)
    on_disk = json.loads(tmp_roll_state.read_text())
    assert on_disk["bytes_printed"] == 500


def test_add_bytes_is_cumulative(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(300)
    tracker.add_bytes(200)
    assert tracker.state["bytes_printed"] == 500


def test_state_survives_reload(tmp_roll_state):
    tracker1 = RollTracker.load(tmp_roll_state)
    tracker1.add_bytes(9999)
    tracker2 = RollTracker.load(tmp_roll_state)
    assert tracker2.state["bytes_printed"] == 9999


def test_reset_clears_bytes_and_updates_dimensions(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(5000)
    tracker.reset(57, 35)
    assert tracker.state["bytes_printed"] == 0
    assert tracker.state["roll_diameter_mm"] == 35
    assert tracker.state["last_reset"] is not None


def test_estimate_remaining_full_roll(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    assert tracker.estimate_remaining() == 100


def test_estimate_remaining_decreases_with_bytes(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(1000)
    assert tracker.estimate_remaining() < 100


def test_estimate_remaining_never_below_zero(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(10_000_000)  # way more than any roll
    assert tracker.estimate_remaining() == 0


def test_save_uses_atomic_write(tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    tracker.add_bytes(42)
    # No .tmp file should remain after save
    assert not tmp_roll_state.with_suffix(".tmp").exists()
