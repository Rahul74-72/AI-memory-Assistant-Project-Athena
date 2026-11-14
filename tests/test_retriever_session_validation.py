from unittest.mock import MagicMock, patch

import pytest

from app.retrieval.retriever import MemoryRetriever


@pytest.mark.parametrize("user_id", [True, False, 0, -1, None, "42", 1.0])
def test_invalid_user_id_does_not_open_database_session(user_id):
    with patch("app.retrieval.retriever.SessionLocal") as factory:
        with pytest.raises(ValueError, match="Valid user_id required"):
            MemoryRetriever(user_id)
        factory.assert_not_called()


def test_valid_user_id_opens_and_closes_owned_session():
    session = MagicMock()
    with patch("app.retrieval.retriever.SessionLocal", return_value=session) as factory:
        retriever = MemoryRetriever(42)
    assert retriever.user_id == 42
    assert retriever.session is session
    factory.assert_called_once_with()
    retriever.close()
    session.close.assert_called_once_with()
