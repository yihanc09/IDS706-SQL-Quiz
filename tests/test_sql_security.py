import pytest

from database import run_query


def test_select_query_allowed():
    """Normal SELECT queries should execute successfully."""
    result = run_query("SELECT COUNT(*) AS total_artists FROM chinook.artist")

    assert result.iloc[0]["total_artists"] == 275


def test_create_table_blocked():
    """Students must not be able to create tables."""
    with pytest.raises(Exception):
        run_query("CREATE TABLE chinook.test_security (id INTEGER)")


def test_delete_blocked():
    """Students must not be able to delete database records."""
    with pytest.raises(Exception):
        run_query("DELETE FROM chinook.artist WHERE artist_id = 1")


def test_update_blocked():
    """Students must not be able to modify database records."""
    with pytest.raises(Exception):
        run_query("UPDATE chinook.artist " "SET name = 'Changed' WHERE artist_id = 1")


def test_multiple_statements_blocked():
    """Multiple SQL statements must not bypass read-only protection."""
    with pytest.raises(Exception):
        run_query("SELECT 1; DELETE FROM chinook.artist WHERE artist_id = 1")


def test_answer_table_not_readable():
    """The quiz database role must not read saved student answers."""
    with pytest.raises(Exception):
        run_query("SELECT * FROM public.quiz_answers")
