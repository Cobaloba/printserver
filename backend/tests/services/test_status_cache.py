import time
import pytest
from app.services.status_cache import StatusCache
from app.exceptions import PrinterError


def test_initial_state_is_offline():
    cache = StatusCache()
    state = cache.get_cached()
    assert state["printer_online"] is False
    assert state["paper_near_end"] is False
    assert state["paper_out"] is False
    assert state["estimated_remaining_pct"] == 0


def test_start_does_not_raise_when_printer_raises(mock_printer):
    mock_printer.configure_status_error(PrinterError("unavailable"))
    cache = StatusCache()
    cache.start(mock_printer)  # must not raise
    time.sleep(0.2)  # let first poll happen
    state = cache.get_cached()
    assert state["printer_online"] is False


def test_cache_populates_after_polling(mock_printer):
    cache = StatusCache()
    cache.start(mock_printer)
    time.sleep(6)  # wait for at least one poll cycle
    assert cache.get_cached()["printer_online"] is True


def test_get_cached_returns_copy():
    cache = StatusCache()
    a = cache.get_cached()
    b = cache.get_cached()
    assert a is not b  # independent copies
