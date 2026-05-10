import pytest
from app.services.printer import MockPrinter
from app.exceptions import PrinterError


def test_mock_print_todo_records_call(mock_printer):
    mock_printer.print_todo("My List", ["Buy milk", "Call Bob"])
    assert any(c[0] == "print_todo" for c in mock_printer._calls)


def test_mock_print_todo_returns_positive_bytes(mock_printer):
    mock_printer.print_todo("Test", ["item"])
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_receipt_records_call(mock_printer):
    mock_printer.print_receipt("Shop", [("Coffee", 2.50)], None, None, 0)
    assert any(c[0] == "print_receipt" for c in mock_printer._calls)


def test_mock_print_receipt_returns_positive_bytes(mock_printer):
    mock_printer.print_receipt("Harrods", [("Gold watch", 340.00)], None, None, 20)
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_free_text(mock_printer):
    mock_printer.print_free_text("Hello world", "medium")
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_qr(mock_printer):
    mock_printer.print_qr("https://example.com")
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_goatse(mock_printer):
    mock_printer.print_goatse()
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_get_status_returns_online(mock_printer):
    status = mock_printer.get_status()
    assert status["printer_online"] is True
    assert "paper_near_end" in status
    assert "paper_out" in status


def test_mock_configure_error_raises_on_next_call(mock_printer):
    mock_printer.configure_error(PrinterError("USB error"))
    with pytest.raises(PrinterError, match="USB error"):
        mock_printer.print_todo("Test", ["item"])


def test_mock_error_clears_after_one_call(mock_printer):
    mock_printer.configure_error(PrinterError("once"))
    with pytest.raises(PrinterError):
        mock_printer.print_goatse()
    # Should not raise on the next call
    mock_printer.print_goatse()
    assert mock_printer.get_bytes_for_job() > 0
