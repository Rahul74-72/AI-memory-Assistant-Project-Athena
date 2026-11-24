from types import SimpleNamespace

from app.retrieval.retriever import MemoryRetriever


def test_relevance_outweighs_importance_when_ranking_memories():
    def memory(value, importance):
        return SimpleNamespace(
            subject="", relation="", value=value, category="", importance=importance,
        )

    words = MemoryRetriever._search_words("machine learning")
    more_relevant = MemoryRetriever._score_memory(memory("machine learning", 1), words)
    more_important = MemoryRetriever._score_memory(memory("machine", 100), words)
    assert more_relevant == (4, 1)
    assert more_important == (2, 100)
    assert more_relevant > more_important
