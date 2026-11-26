from types import SimpleNamespace
from unittest.mock import MagicMock

from app.retrieval.retriever import MemoryRetriever


def test_high_importance_cannot_promote_a_nonmatching_memory():
    retriever = MemoryRetriever.__new__(MemoryRetriever)
    retriever.user_id = 42
    unrelated = SimpleNamespace(
        id=1, subject="Gardening", relation="likes", value="flowers",
        category="hobby", importance=100,
    )
    matching = SimpleNamespace(
        id=2, subject="Athena", relation="is", value="assistant",
        category="project", importance=1,
    )
    retriever.session = MagicMock()
    retriever.session.execute.return_value.scalars.return_value.all.return_value = [
        unrelated, matching,
    ]
    assert retriever.search("Athena", limit=1) == [matching]
    assert retriever.search("Athena") == [matching]
