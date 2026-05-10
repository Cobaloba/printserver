import pytest
from app.services.printer import MockPrinter


@pytest.fixture
def mock_printer() -> MockPrinter:
    return MockPrinter()


@pytest.fixture
def tmp_roll_state(tmp_path):
    return tmp_path / "roll_state.json"
