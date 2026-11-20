from types import SimpleNamespace

from app.retrieval.retriever import MemoryRetriever


def test_query_order_and_repetition_do_not_change_relevance():
    memory = SimpleNamespace(
        subject="Athena", relation="supports", value="machine learning",
        category="project", importance=7,
    )
    baseline = MemoryRetriever._score_memory(
        memory, MemoryRetriever._search_words("Athena machine learning")
    )
    repeated = MemoryRetriever._score_memory(
        memory, MemoryRetriever._search_words("learning ATHENA machine Athena learning")
    )
    assert baseline == (7, 7)
    assert repeated == baseline
