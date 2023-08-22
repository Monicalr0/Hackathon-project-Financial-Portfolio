import pytest
import sys
import os
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

# get the parent directory of the current file
parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# add the parent directory to the system path
sys.path.append(parent)
print(sys.path)

from flaskr.db_api import DatabaseEditor

global pos_tickers, neg_tickers
pos_tickers = ["AAPL", "TSLA", "MSFT"]
neg_tickers = ["PLTR", "GOOG", "VOO"]


@pytest.fixture
def empty_db_editor():
    """
    db_editor_resource Fixture for DatabaseEditor.

    Yields:
        DatabaseEditor: An empty DatabaseEditor resource to use in tests.
    """
    # setup
    db_editor = DatabaseEditor(password=DB_PASSWORD, database="test_team11")
    yield db_editor
    # teardown
    db_editor.close_editor()


@pytest.fixture
def full_db_editor():
    """
    db_editor_resource Fixture for DatabaseEditor.

    Yields:
        DatabaseEditor: A DatabaseEditor resource with data in it to use in tests.
    """
    # setup
    db_editor = DatabaseEditor(password=DB_PASSWORD, database="test_team11")
    db_editor.add_tickers(pos_tickers)
    yield db_editor
    # teardown
    db_editor.close_editor()


@pytest.mark.parametrize(
    "ticker_id, expected",
    [
        ("AAPL", True),
        ("TSLA", True),
        ("MSFT", True),
        ("FFET", False),
        ("ZZOE", False),
        ("LPOL", False),
    ],
)
def test_is_valid_ticker(
    empty_db_editor: DatabaseEditor, ticker_id: str, expected: bool
):
    """
    test_is_valid_ticker Test the is_valid_ticker method of DatabaseEditor.

    Args:
        db_editor_resource (DatabaseEditor): DatabaseEditor resource.
        ticker_id (str): Ticker to test.
        expected (bool): Expected result of the test.
    """
    # check
    assert empty_db_editor.is_valid_ticker(ticker_id) == expected


@pytest.mark.parametrize(
    "ticker_id, expected",
    [
        ("AAPL", True),
        ("TSLA", True),
        ("MSFT", True),
    ],
)
def test_add_ticker(empty_db_editor: DatabaseEditor, ticker_id: str, expected: bool):
    """
    test_add_ticker Test the add_ticker method of DatabaseEditor.

    Args:
        db_editor_resource (DatabaseEditor): DatabaseEditor resource.
        ticker_id (str): Ticker to test.
        expected (bool): Expected result of the test.
    """
    # check
    empty_db_editor.add_ticker(ticker_id)
    assert (ticker_id in empty_db_editor.get_tickers()) == expected


@pytest.mark.parametrize(
    "ticker_ids, expected",
    [
        (pos_tickers, True),
        (neg_tickers, False),
    ],
)
def test_add_tickers(empty_db_editor: DatabaseEditor, ticker_ids: list, expected: bool):
    """
    test_add_tickers Test the add_tickers method of DatabaseEditor.

    Args:
        empty_db_editor (DatabaseEditor): DatabaseEditor resource.
        ticker_ids (list): Tickers to test.
        expected (bool): Expected result of the test.
    """
    # check
    empty_db_editor.add_tickers(pos_tickers)
    test_result = sorted(empty_db_editor.get_tickers())
    assert (test_result == sorted(ticker_ids)) == expected


def test_add_ticker_data(full_db_editor: DatabaseEditor):
    """
    test_add_ticker_data Test the add_ticker_data method of DatabaseEditor.

    Args:
        full_db_editor (DatabaseEditor): DatabaseEditor resource.
    """
    # check
    full_db_editor.add_ticker_data("AAPL", 100, "2021-01-01")
    assert ("AAPL", 100, "2021-01-01") in full_db_editor.get_ticker_data("AAPL")
