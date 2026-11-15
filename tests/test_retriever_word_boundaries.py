from types import SimpleNamespace

import pytest

from app.retrieval.retriever import MemoryRetriever


@pytest.mark.parametrize("field,weight", [
    ("subject", 3), ("relation", 3), ("value", 2), ("category", 1),
])
def test_scoring_matches_whole_words_in_every_field(field, weight):
    values = dict(subject="", relation="", value="", category="", importance=5)
    values[field] = "learning"
    memory = SimpleNamespace(**values)
    words = MemoryRetriever._search_words("learn")
    assert MemoryRetriever._score_memory(memory, words) == (0, 5)

    values[field] = "LEARN_project, learn!"
    memory = SimpleNamespace(**values)
    assert MemoryRetriever._score_memory(memory, words) == (weight, 5)
