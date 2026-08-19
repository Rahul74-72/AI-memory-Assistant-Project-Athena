from types import SimpleNamespace

from app.retrieval.retriever import MemoryRetriever


def make_memory(**overrides):
    values = {
        "subject": "Rahul",
        "relation": "likes",
        "value": "machine learning",
        "category": "preference",
        "importance": 5,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_score_memory_counts_unique_matching_words():
    memory = make_memory(value="machine learning project")

    assert MemoryRetriever._score_memory(
        memory,
        ["machine", "learning", "machine", "database"],
    ) == (2, 5)


def test_score_memory_uses_importance_as_tie_breaker():
    low = make_memory(value="machine learning", importance=2)
    high = make_memory(value="machine learning", importance=9)
    words = ["machine", "learning"]

    assert MemoryRetriever._score_memory(low, words) < MemoryRetriever._score_memory(
        high, words
    )


def test_score_memory_searches_subject_and_category():
    memory = make_memory(subject="Athena", category="project")

    assert MemoryRetriever._score_memory(
        memory,
        ["athena", "project"],
    ) == (2, 5)
