from types import SimpleNamespace

from app.retrieval.retriever import MemoryRetriever


def test_empty_memory_fields_do_not_match_and_missing_importance_is_zero():
    memory = SimpleNamespace(
        subject=None, relation="", value=None, category="", importance=None,
    )
    assert MemoryRetriever._score_memory(memory, ["athena"]) == (0, 0)


def test_missing_fields_do_not_hide_a_valid_value_match():
    memory = SimpleNamespace(
        subject=None, relation=None, value="Athena", category=None, importance=None,
    )
    assert MemoryRetriever._score_memory(memory, ["athena"]) == (2, 0)
