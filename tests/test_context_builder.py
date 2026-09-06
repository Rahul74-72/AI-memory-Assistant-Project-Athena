import pytest

from app.context.context_builder import MemoryContextBuilder


class Memory:
    subject = "Rahul"
    relation = "likes"
    value = "Python"


def test_context_builder_rejects_invalid_max_memories():
    with pytest.raises(TypeError):
        MemoryContextBuilder(max_memories="5")

    with pytest.raises(ValueError):
        MemoryContextBuilder(max_memories=-1)


def test_context_builder_zero_limit_returns_empty_context_message():
    builder = MemoryContextBuilder(max_memories=0)

    result = builder.build([{"memory": Memory(), "score": 0.9}])

    assert result == "No relevant memories were found."


def test_context_builder_caps_context_to_configured_limit():
    class First:
        subject = "Rahul"
        relation = "likes"
        value = "Python"

    class Second:
        subject = "Rahul"
        relation = "studies"
        value = "AI"

    builder = MemoryContextBuilder(max_memories=1)
    result = builder.build([
        {"memory": First(), "score": 0.9},
        {"memory": Second(), "score": 0.8},
    ])

    assert result == "- Rahul likes Python"
