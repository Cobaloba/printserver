import pytest
from app.services import print_service
from app.exceptions import PrinterError


def test_print_todo_succeeds(mock_printer):
    print_service.print_todo(mock_printer, "TO DO", ["Buy milk", "Call Bob"])
    assert mock_printer.get_bytes_for_job() > 0


def test_print_todo_records_call(mock_printer):
    print_service.print_todo(mock_printer, "My List", ["item1"])
    assert any(c[0] == "print_todo" for c in mock_printer._calls)


def test_print_receipt_succeeds(mock_printer):
    print_service.print_receipt(
        mock_printer, "Harrods", [("Gold watch", 340.00)], None, None, 20
    )
    assert mock_printer.get_bytes_for_job() > 0


def test_print_receipt_records_call(mock_printer):
    print_service.print_receipt(mock_printer, "Shop", [("Item", 1.0)], None, None, 0)
    assert any(c[0] == "print_receipt" for c in mock_printer._calls)


def test_print_goatse_succeeds(mock_printer):
    print_service.print_goatse(mock_printer)
    assert mock_printer.get_bytes_for_job() > 0


def test_print_todo_propagates_printer_error(mock_printer):
    mock_printer.configure_error(PrinterError("USB disconnected"))
    with pytest.raises(PrinterError, match="USB disconnected"):
        print_service.print_todo(mock_printer, "Test", ["item"])


def test_print_receipt_propagates_printer_error(mock_printer):
    mock_printer.configure_error(PrinterError("paper out"))
    with pytest.raises(PrinterError):
        print_service.print_receipt(mock_printer, "Shop", [("x", 1.0)], None, None, 0)


def test_print_goatse_propagates_printer_error(mock_printer):
    mock_printer.configure_error(PrinterError("offline"))
    with pytest.raises(PrinterError):
        print_service.print_goatse(mock_printer)


def test_print_free_text_small(mock_printer):
    print_service.print_free_text(mock_printer, "Hello", "small")
    assert any(c[0] == "print_free_text" for c in mock_printer._calls)
    assert mock_printer.get_bytes_for_job() > 0


def test_print_free_text_medium(mock_printer):
    print_service.print_free_text(mock_printer, "Hello", "medium")
    call = next(c for c in mock_printer._calls if c[0] == "print_free_text")
    assert call[1][1] == "medium"


def test_print_free_text_large(mock_printer):
    print_service.print_free_text(mock_printer, "Hello", "large")
    call = next(c for c in mock_printer._calls if c[0] == "print_free_text")
    assert call[1][1] == "large"


def test_print_qr_succeeds(mock_printer):
    print_service.print_qr(mock_printer, "https://example.com")
    assert mock_printer.get_bytes_for_job() > 0


def test_print_qr_records_call(mock_printer):
    print_service.print_qr(mock_printer, "https://example.com")
    assert any(c[0] == "print_qr" for c in mock_printer._calls)


def test_print_free_text_propagates_printer_error(mock_printer):
    mock_printer.configure_error(PrinterError("paper jam"))
    with pytest.raises(PrinterError):
        print_service.print_free_text(mock_printer, "text", "small")


def test_print_qr_propagates_printer_error(mock_printer):
    mock_printer.configure_error(PrinterError("offline"))
    with pytest.raises(PrinterError):
        print_service.print_qr(mock_printer, "https://example.com")
