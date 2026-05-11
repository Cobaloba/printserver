import pytest
from unittest.mock import MagicMock, patch
from app.services.telegram_bot import TelegramBot
from app.services.printer import MockPrinter
from app.exceptions import PrinterError


def make_update(update_id, text, chat_id=99):
    return {
        "update_id": update_id,
        "message": {"text": text, "chat": {"id": chat_id}},
    }


@pytest.fixture
def bot():
    return TelegramBot("fake-token")


@pytest.fixture
def printer():
    return MockPrinter()


@pytest.fixture
def ctx():
    return MagicMock()


def test_print_free_text_command(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "print: Hello world"), printer, ctx)
    assert sent == ["Printing ✓"]
    assert any(c[0] == "print_free_text" for c in printer._calls)


def test_print_free_text_case_insensitive(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "Print: Hello"), printer, ctx)
    assert sent == ["Printing ✓"]


def test_print_free_text_empty_body(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "print:"), printer, ctx)
    assert "Usage" in sent[0]
    assert printer._calls == []


def test_print_todo_command(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "print todo: Shopping | Milk | Eggs"), printer, ctx)
    assert sent == ["Printing ✓"]
    calls = [c for c in printer._calls if c[0] == "print_todo"]
    assert len(calls) == 1
    _, args, _ = calls[0]
    assert args[0] == "Shopping"
    assert list(args[1]) == ["Milk", "Eggs"]


def test_print_todo_no_items(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "print todo: Just a title"), printer, ctx)
    assert "Usage" in sent[0]
    assert printer._calls == []


def test_printer_error_reported(bot, printer, ctx):
    printer.configure_error(PrinterError("offline"))
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "print: Hello"), printer, ctx)
    assert "Printer error" in sent[0]


def test_unknown_command_shows_help(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update(make_update(1, "hello there"), printer, ctx)
    assert "PrintServer bot" in sent[0]
    assert printer._calls == []


def test_empty_message_ignored(bot, printer, ctx):
    sent = []
    with patch.object(bot, "_send", side_effect=lambda cid, text, c: sent.append(text)):
        bot._handle_update({"update_id": 1, "message": {"chat": {"id": 1}}}, printer, ctx)
    assert sent == []
