from types import SimpleNamespace

from app.retrieval.retriever import MemoryRetriever


def test_query_word_is_scored_once_at_its_strongest_field():
    memory = SimpleNamespace(
        subject="Athena",
        relation="likes",
        value="Athena",
        category="project",
        importance=5,
    )

    assert MemoryRetriever._score_memory(memory, ["athena"]) == (3, 5)
