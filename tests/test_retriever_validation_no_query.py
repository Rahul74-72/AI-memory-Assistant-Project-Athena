from unittest.mock import MagicMock

import pytest

from app.retrieval.retriever import MemoryRetriever


@pytest.mark.parametrize("limit,error", [
    (-1, ValueError), (True, TypeError), (1.5, TypeError), ("2", TypeError),
])
def test_invalid_limit_is_rejected_before_database_access(limit, error):
    retriever = MemoryRetriever.__new__(MemoryRetriever)
    retriever.user_id = 42
    retriever.session = MagicMock()
    with pytest.raises(error):
        retriever.search("Athena", limit=limit)
    retriever.session.execute.assert_not_called()
