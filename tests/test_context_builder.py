
import pytest

from app.context.context_builder import MemoryContextBuilder


class Memory:
    subject = "Rahul"
    relation = "likes"
    value = "Python"


def test_context_builder_rejects_invalid_max_memories():
    with pytest.raises(TypeError):
        MemoryContextBuilder(max_memories="5")

    with pytest.raises(TypeError):
        MemoryContextBuilder(max_memories=True)

    with pytest.raises(ValueError):
        MemoryContextBuilder(max_memories=-1)


def test_context_builder_zero_limit_returns_empty_context_message():
    builder = MemoryContextBuilder(max_memories=0)

    result = builder.build(
        [{"memory": Memory(), "score": 0.9}],
        user_question="What programming language does Rahul like?",
    )

    assert result == "No sufficient evidence was found."


def test_context_builder_empty_memory_list_returns_empty_context_message():
    result = MemoryContextBuilder().build(
        [],
        user_question="What programming language does Rahul like?",
    )

    assert result == "No sufficient evidence was found."


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
    result = builder.build(
        [
            {"memory": First(), "score": 0.9, "semantic_score": 0.9},
            {"memory": Second(), "score": 0.8, "semantic_score": 0.8},
        ],
        user_question="What programming language does Rahul like?",
    )

    assert result.startswith("- Rahul likes Python ")
    assert "evidence=" in result
    assert "AI" not in result



def test_context_builder_formats_underscored_relationships():
    class Job:
        subject = "Rahul"
        relation = "current_job"
        value = "AI Engineer"

    builder = MemoryContextBuilder()

    result = builder.build(
        [
            {
                "memory": Job(),
                "score": 0.9,
                "semantic_score": 0.9,
            }
        ],
        user_question="What is Rahul's current job?",
    )

    assert result.startswith("- Rahul current job AI Engineer ")
    assert "evidence=high" in result


def test_context_builder_default_limit_allows_five_memories():
    memories = [
        {
            "memory": type("Memory", (), {
                "subject": f"Person {index}",
                "relation": "likes",
                "value": "Python",
            })(),
            "score": 1.0,
        }
        for index in range(6)
    ]

    result = MemoryContextBuilder().build(
        memories,
        user_question="What do these people like?",
    )

    assert len(result.splitlines()) <= 5
