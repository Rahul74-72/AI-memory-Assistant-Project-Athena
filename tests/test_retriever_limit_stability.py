from types import SimpleNamespace
from unittest.mock import MagicMock

from app.retrieval.retriever import MemoryRetriever


def test_limit_selects_same_memory_when_database_row_order_changes():
    retriever = MemoryRetriever.__new__(MemoryRetriever)
    retriever.user_id = 42
    memories = [
        SimpleNamespace(id=key, subject="Athena", relation="", value="",
                        category="", importance=5)
        for key in [30, 10, 20]
    ]
    retriever.session = MagicMock()
    rows = retriever.session.execute.return_value.scalars.return_value
    rows.all.return_value = memories
    first = retriever.search("Athena", limit=1)
    rows.all.return_value = list(reversed(memories))
    second = retriever.search("Athena", limit=1)
    assert [memory.id for memory in first] == [10]
    assert second == first
    assert [memory.id for memory in memories] == [30, 10, 20]
