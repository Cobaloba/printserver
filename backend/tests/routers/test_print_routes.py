import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_printer, get_roll_tracker
from app.services.roll_tracker import RollTracker
from app.exceptions import PrinterError


@pytest.fixture
def client(mock_printer, tmp_roll_state):
    tracker = RollTracker.load(tmp_roll_state)
    app.dependency_overrides[get_printer] = lambda: mock_printer
    app.dependency_overrides[get_roll_tracker] = lambda: tracker
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── Todo ───────────────────────────────────────────────────────────────────────

def test_print_todo_success(client):
    r = client.post("/api/v1/print/todo", json={"title": "My List", "items": ["item1"]})
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_print_todo_empty_items_returns_422(client):
    r = client.post("/api/v1/print/todo", json={"items": []})
    assert r.status_code == 422


def test_print_todo_missing_items_returns_422(client):
    r = client.post("/api/v1/print/todo", json={"title": "Test"})
    assert r.status_code == 422


def test_print_todo_printer_error_returns_503(client, mock_printer):
    mock_printer.configure_error(PrinterError("USB disconnected"))
    r = client.post("/api/v1/print/todo", json={"items": ["item1"]})
    assert r.status_code == 503
    assert "USB disconnected" in r.json()["detail"]


# ── Receipt ────────────────────────────────────────────────────────────────────

def test_print_receipt_success(client):
    r = client.post("/api/v1/print/receipt", json={
        "store": "Shop",
        "items": [{"name": "Coffee", "price": 2.50}],
    })
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_print_receipt_printer_error_returns_503(client, mock_printer):
    mock_printer.configure_error(PrinterError("paper out"))
    r = client.post("/api/v1/print/receipt", json={
        "store": "Shop",
        "items": [{"name": "Item", "price": 1.0}],
    })
    assert r.status_code == 503


# ── Free text ──────────────────────────────────────────────────────────────────

def test_print_free_text_success(client):
    r = client.post("/api/v1/print/free-text", json={"text": "Hello world"})
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_print_free_text_printer_error_returns_503(client, mock_printer):
    mock_printer.configure_error(PrinterError("offline"))
    r = client.post("/api/v1/print/free-text", json={"text": "test"})
    assert r.status_code == 503


# ── QR ─────────────────────────────────────────────────────────────────────────

def test_print_qr_success(client):
    r = client.post("/api/v1/print/qr", json={"url": "https://example.com"})
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_print_qr_printer_error_returns_503(client, mock_printer):
    mock_printer.configure_error(PrinterError("error"))
    r = client.post("/api/v1/print/qr", json={"url": "https://example.com"})
    assert r.status_code == 503


# ── Goatse ─────────────────────────────────────────────────────────────────────

def test_print_goatse_success(client):
    r = client.post("/api/v1/print/goatse")
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_print_goatse_printer_error_returns_503(client, mock_printer):
    mock_printer.configure_error(PrinterError("error"))
    r = client.post("/api/v1/print/goatse")
    assert r.status_code == 503
