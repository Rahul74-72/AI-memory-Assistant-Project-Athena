from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

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
    ) == (4, 5)


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
    ) == (4, 5)


def test_score_memory_prefers_subject_match_over_category_match():
    subject_match = make_memory(subject="Athena", category="other")
    category_match = make_memory(subject="Other", category="Athena")

    assert MemoryRetriever._score_memory(
        subject_match, ["athena"]
    ) > MemoryRetriever._score_memory(category_match, ["athena"])


def test_search_can_limit_ranked_results():
    retriever = MemoryRetriever.__new__(MemoryRetriever)
    memories = [
        make_memory(subject="Athena", importance=5),
        make_memory(subject="Athena", importance=9),
        make_memory(subject="Athena", importance=1),
    ]

    result = MagicMock()
    result.scalars.return_value.all.return_value = memories
    retriever.session = MagicMock()
    retriever.session.execute.return_value = result

    ranked = retriever.search("Athena", limit=2)

    assert len(ranked) == 2
    assert ranked == [memories[1], memories[0]]


def test_search_rejects_negative_limit():
    retriever = MemoryRetriever.__new__(MemoryRetriever)
    retriever.session = MagicMock()

    with pytest.raises(ValueError, match="non-negative"):
        retriever.search("Athena", limit=-1)
