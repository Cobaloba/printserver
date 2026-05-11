import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_printer, get_roll_tracker, get_status_cache
from app.services.roll_tracker import RollTracker


@pytest.fixture
def client(mock_printer, tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    app.dependency_overrides[get_printer] = lambda: mock_printer
    app.dependency_overrides[get_roll_tracker] = lambda: tracker
    with TestClient(app) as c:
        yield c, tracker
    app.dependency_overrides.clear()


def test_get_roll_state_returns_expected_fields(client):
    c, _ = client
    r = c.get("/api/v1/admin/roll")
    assert r.status_code == 200
    data = r.json()
    assert "bytes_printed" in data
    assert "roll_width_mm" in data
    assert "roll_diameter_mm" in data
    assert "last_reset" in data
    assert "estimated_remaining_pct" in data


def test_get_roll_state_initial_values(client):
    c, _ = client
    r = c.get("/api/v1/admin/roll")
    data = r.json()
    assert data["bytes_printed"] == 0
    assert data["roll_width_mm"] == 57
    assert data["roll_diameter_mm"] == 40
    assert data["estimated_remaining_pct"] == 100


def test_reset_roll_returns_success(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": 57, "diameter_mm": 35})
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_reset_roll_updates_state(client, tmp_roll_state):
    import json
    c, tracker = client
    c.post("/api/v1/admin/roll", json={"width_mm": 57, "diameter_mm": 35})
    assert tracker.state["roll_diameter_mm"] == 35
    assert tracker.state["bytes_printed"] == 0
    on_disk = json.loads(tmp_roll_state.read_text())
    assert on_disk["roll_diameter_mm"] == 35


def test_reset_roll_missing_width_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"diameter_mm": 40})
    assert r.status_code == 422


def test_reset_roll_missing_diameter_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": 57})
    assert r.status_code == 422


def test_reset_roll_zero_width_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": 0, "diameter_mm": 40})
    assert r.status_code == 422


def test_reset_roll_negative_width_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": -1, "diameter_mm": 40})
    assert r.status_code == 422


def test_reset_roll_zero_diameter_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": 57, "diameter_mm": 0})
    assert r.status_code == 422


def test_reset_roll_negative_diameter_returns_422(client):
    c, _ = client
    r = c.post("/api/v1/admin/roll", json={"width_mm": 57, "diameter_mm": -5})
    assert r.status_code == 422


def test_reset_then_verify_flow(client):
    c, tracker = client
    # Add some bytes to simulate usage
    tracker.add_bytes(5000)
    assert tracker.state["bytes_printed"] == 5000
    # Reset via API
    r = c.post("/api/v1/admin/roll", json={"width_mm": 57, "diameter_mm": 40})
    assert r.status_code == 200
    # Verify via GET
    r2 = c.get("/api/v1/admin/roll")
    assert r2.json()["bytes_printed"] == 0
    assert r2.json()["estimated_remaining_pct"] == 100
