import pytest
from app.services.print_service import sanitize_text


def test_plain_ascii_unchanged():
    assert sanitize_text("Hello world") == "Hello world"


def test_emoji_replaced_with_bracketed_name():
    result = sanitize_text("Hi \U0001f600 world")  # 😀 grinning face
    assert result == "Hi [grinning face] world"


def test_heart_emoji():
    result = sanitize_text("I ❤️ this")  # ❤️
    assert "[" in result and "]" in result
    assert "heart" in result.lower()


def test_thumbs_up():
    result = sanitize_text("\U0001f44d great")  # 👍
    assert "thumbs" in result.lower()


def test_accented_chars_transliterated():
    assert sanitize_text("caf\xe9") == "cafe"       # café → cafe
    assert sanitize_text("na\xefve") == "naive"     # naïve → naive
    assert sanitize_text("r\xe9sum\xe9") == "resume"


def test_german_chars():
    assert sanitize_text("\xfcber") == "uber"        # über → uber
    assert sanitize_text("Stra\xdfe") == "Strae"     # Straße → Strae (sharp-s has no direct ASCII)


def test_cjk_dropped_silently():
    result = sanitize_text("日本語")     # 日本語
    assert result == ""


def test_mixed_emoji_and_accents():
    result = sanitize_text("caf\xe9 \U0001f600")     # café 😀
    assert result == "cafe [grinning face]"


def test_empty_string():
    assert sanitize_text("") == ""


def test_numbers_punctuation_preserved():
    assert sanitize_text("2x £3.50 = £7.00!") == "2x 3.50 = 7.00!"


def test_todo_sanitizes_title_and_items(mock_printer):
    from app.services.print_service import print_todo
    print_todo(mock_printer, "caf\xe9 run \U0001f600", ["Buy milk \U0001f95b", "Eggs"])
    calls = [c for c in mock_printer._calls if c[0] == "print_todo"]
    assert len(calls) == 1
    _, args, _ = calls[0]
    assert args[0] == "cafe run [grinning face]"
    assert args[1][0] == "Buy milk [glass of milk]"
    assert args[1][1] == "Eggs"


def test_free_text_sanitized(mock_printer):
    from app.services.print_service import print_free_text
    print_free_text(mock_printer, "Hello \U0001f44d", "medium")
    calls = [c for c in mock_printer._calls if c[0] == "print_free_text"]
    assert "thumbs" in calls[0][1][0].lower()


def test_receipt_store_and_items_sanitized(mock_printer):
    from app.services.print_service import print_receipt
    print_receipt(mock_printer, "Caf\xe9 \U0001f375", [("Latt\xe9", 3.50)], None, None, 0)
    calls = [c for c in mock_printer._calls if c[0] == "print_receipt"]
    _, args, _ = calls[0]
    assert args[0] == "Cafe [teacup without handle]"
    assert args[1][0][0] == "Latte"


def test_qr_url_not_sanitized(mock_printer):
    from app.services.print_service import print_qr
    url = "https://example.com/path?q=1&r=2"
    print_qr(mock_printer, url)
    calls = [c for c in mock_printer._calls if c[0] == "print_qr"]
    assert calls[0][1][0] == url  # URL unchanged
