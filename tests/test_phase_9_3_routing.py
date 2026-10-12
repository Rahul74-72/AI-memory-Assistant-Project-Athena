
import ast
from pathlib import Path


CHAT_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "chat"
    / "chat.py"
)


def get_chat_engine_method(method_name):
    tree = ast.parse(
        CHAT_SOURCE.read_text(encoding="utf-8")
    )

    chat_engine = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ChatEngine"
    )

    return next(
        node
        for node in chat_engine.body
        if isinstance(node, ast.FunctionDef)
        and node.name == method_name
    )


def test_historical_date_extractor_supports_year_interval():
    method = get_chat_engine_method(
        "extract_historical_date"
    )
    source = ast.unparse(method)

    assert "datetime(year, 1, 1)" in source
    assert "datetime(year + 1, 1, 1)" in source

def test_generate_response_routes_explicit_history():
    method = get_chat_engine_method(
        "generate_response"
    )
    source = ast.unparse(method)

    assert "extract_historical_date" in source
    assert "search_historical_memories" in source
    assert "get_memories_overlapping_interval" not in source



def test_generate_response_preserves_current_semantic_search():
    method = get_chat_engine_method(
        "generate_response"
    )
    source = ast.unparse(method)

    assert "semantic_search" in source
    assert "top_k=3" in source
    assert "threshold=0.2" in source


from datetime import datetime
from types import SimpleNamespace

from app.chat.chat import ChatEngine


def make_chat_engine():
    engine = ChatEngine.__new__(ChatEngine)

    engine.memory = SimpleNamespace(
        get_recent_messages=lambda limit: []
    )

    engine.context_builder = SimpleNamespace(
        build=lambda results, question: (
            "No sufficient evidence was found."
            if not results
            else "test evidence"
        )
    )

    engine.reasoner = SimpleNamespace(
        answer=lambda **kwargs: kwargs["memory_context"],
        answer_general=lambda **kwargs: "general answer",
    )

    engine.memory_store = SimpleNamespace(
        historical_calls=[],
        semantic_calls=[],
    )

    def historical_search(query, start, end, **kwargs):
        engine.memory_store.historical_calls.append(
            (query, start, end, kwargs)
        )
        return []

    def semantic_search(query, **kwargs):
        engine.memory_store.semantic_calls.append(
            (query, kwargs)
        )
        return []

    engine.memory_store.search_historical_memories = historical_search
    engine.memory_store.semantic_search = semantic_search

    return engine


def test_dated_residence_question_uses_historical_search():
    engine = make_chat_engine()

    response = engine.generate_response(
        "Where did I live in 2024?"
    )

    assert len(engine.memory_store.historical_calls) == 1
    assert engine.memory_store.semantic_calls == []

    _, start, end, kwargs = (
        engine.memory_store.historical_calls[0]
    )

    assert start == datetime(2024, 1, 1)
    assert end == datetime(2025, 1, 1)
    assert kwargs["relation"] == "lives_in"
    assert response == "No sufficient evidence was found."


def test_current_residence_question_uses_semantic_search():
    engine = make_chat_engine()

    engine.generate_response("Where do I live?")

    assert engine.memory_store.historical_calls == []
    assert len(engine.memory_store.semantic_calls) == 1

    query, kwargs = engine.memory_store.semantic_calls[0]

    assert query == "Where do I live?"
    assert kwargs["top_k"] == 3
    assert kwargs["threshold"] == 0.20

def test_historical_date_extractor_rejects_invalid_iso_date():
    engine = ChatEngine.__new__(ChatEngine)

    result = engine.extract_historical_date(
        "Where did I live in 2024-02-30?"
    )

    assert result is None


def test_historical_question_without_date_does_not_use_current_search():
    engine = make_chat_engine()

    engine.generate_response(
        "Where did I live previously?"
    )

    assert engine.memory_store.historical_calls == []
    assert engine.memory_store.semantic_calls == []
