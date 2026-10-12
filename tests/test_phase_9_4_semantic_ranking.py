
from datetime import datetime
from pathlib import Path
import json
import tempfile

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Memory
from app.memory.memory_store import MemoryStore


class FakeEmbeddings:
    def create_embedding(self, text):
        text = text.lower()
        if "where" in text or "live" in text:
            return [1.0, 0.0]
        return [0.0, 1.0]

    def serialize(self, embedding):
        return json.dumps(embedding)

    def deserialize(self, embedding):
        return json.loads(embedding)

    def similarity(self, first, second):
        return sum(a * b for a, b in zip(first, second))


class FakeDecay:
    def calculate_effective_importance(
        self, importance, relation, updated_at, current_time
    ):
        return float(importance)


class FakeReinforcement:
    def calculate_reinforcement(
        self, retrieval_count, last_retrieved_at, current_time
    ):
        return 0.0

    def record_retrieval(self, memory, current_time):
        memory.retrieval_count += 1
        memory.last_retrieved_at = current_time


class FakeLifecycle:
    def determine_state(
        self, memory, effective_importance, reinforcement, current_time
    ):
        return memory.lifecycle_state or "active"


class FakeAdaptivePriority:
    def calculate_priority(self, memory, current_time):
        return 0.0


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "semantic_ranking.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=engine)

        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

        instance = MemoryStore.__new__(MemoryStore)
        instance.session = session_factory()
        instance.embedding_manager = FakeEmbeddings()
        instance.memory_decay = FakeDecay()
        instance.memory_reinforcement = FakeReinforcement()
        instance.memory_lifecycle = FakeLifecycle()
        instance.adaptive_prioritization = FakeAdaptivePriority()

        try:
            yield instance
        finally:
            instance.session.close()
            engine.dispose()


def add_memory(
    store,
    *,
    relation="likes",
    value="machine learning",
    importance=5,
    embedding=None,
    lifecycle_state="active",
    updated_at=None,
    retrieval_count=0,
):
    memory = Memory(
        subject="User",
        relation=relation,
        value=value,
        category="test",
        importance=importance,
        active=True,
        lifecycle_state=lifecycle_state,
        embedding=store.embedding_manager.serialize(
            embedding if embedding is not None else [0.0, 1.0]
        ),
        updated_at=(
            updated_at
            if updated_at is not None
            else datetime(2025, 1, 1)
        ),
        created_at=datetime(2025, 1, 1),
        retrieval_count=retrieval_count,
    )
    store.session.add(memory)
    store.session.commit()
    return memory


def test_semantic_search_sorts_by_final_score(store):
    lower = add_memory(
        store, value="machine learning", importance=2
    )
    higher = add_memory(
        store, value="machine learning", importance=9
    )

    results = store.semantic_search(
        "machine learning", threshold=0.0
    )

    assert [item["memory"].id for item in results] == [
        higher.id, lower.id
    ]
    assert results[0]["score"] >= results[1]["score"]


def test_semantic_search_applies_threshold(store):
    add_memory(store, value="unrelated preference")

    results = store.semantic_search(
        "Where do I live?", threshold=0.5
    )

    assert results == []


def test_semantic_search_respects_top_k(store):
    add_memory(store, value="machine learning", importance=3)
    add_memory(store, value="machine learning", importance=6)
    add_memory(store, value="machine learning", importance=9)

    results = store.semantic_search(
        "machine learning", top_k=2, threshold=0.0
    )

    assert len(results) == 2
    assert results[0]["memory"].importance == 9
    assert results[1]["memory"].importance == 6


def test_semantic_search_excludes_archived_memories(store):
    add_memory(
        store,
        value="machine learning",
        lifecycle_state="archived",
    )

    results = store.semantic_search(
        "machine learning", threshold=0.0
    )

    assert results == []


def test_semantic_search_records_only_returned_retrievals(store):
    first = add_memory(store, value="machine learning", importance=9)
    second = add_memory(store, value="machine learning", importance=5)

    results = store.semantic_search(
        "machine learning", top_k=1, threshold=0.0
    )

    store.session.refresh(first)
    store.session.refresh(second)

    assert len(results) == 1
    assert first.retrieval_count == 1
    assert second.retrieval_count == 0

def test_equal_timestamps_do_not_arbitrarily_penalize_conflicting_facts(store):
    timestamp = datetime(2025, 1, 1)

    add_memory(
        store,
        relation="lives_in",
        value="Jaipur",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=timestamp,
    )
    add_memory(
        store,
        relation="lives_in",
        value="Medchal",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=timestamp,
    )

    results = store.semantic_search(
        "Where do I live?",
        threshold=0.0,
    )

    assert len(results) == 2
    assert all(
        result["conflict_penalty"] == 0.0
        for result in results
    )

def test_newer_conflicting_fact_wins_when_timestamps_differ(store):
    older_timestamp = datetime(2024, 1, 1)
    newer_timestamp = datetime(2025, 1, 1)

    add_memory(
        store,
        relation="lives_in",
        value="Jaipur",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=older_timestamp,
    )
    add_memory(
        store,
        relation="lives_in",
        value="Medchal",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=newer_timestamp,
    )

    results = store.semantic_search(
        "Where do I live?",
        threshold=0.0,
    )

    penalties = {
        result["memory"].value: result["conflict_penalty"]
        for result in results
    }

    assert penalties["Jaipur"] == pytest.approx(0.10)
    assert penalties["Medchal"] == pytest.approx(0.0)

def test_tied_latest_conflicting_facts_do_not_penalize_any_candidate(store):
    add_memory(
        store,
        relation="lives_in",
        value="Jaipur",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=datetime(2024, 1, 1),
    )
    add_memory(
        store,
        relation="lives_in",
        value="Medchal",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=datetime(2025, 1, 1),
    )
    add_memory(
        store,
        relation="lives_in",
        value="Hyderabad",
        importance=9,
        embedding=[1.0, 0.0],
        updated_at=datetime(2025, 1, 1),
    )

    results = store.semantic_search(
        "Where do I live?",
        threshold=0.0,
    )

    assert len(results) == 3
    assert all(
        result["conflict_penalty"] == 0.0
        for result in results
    )
def test_strictly_newer_fact_resolves_an_older_timestamp_tie(store):
    add_memory(
        store, relation="lives_in", value="Jaipur", importance=9,
        embedding=[1.0, 0.0], updated_at=datetime(2024, 1, 1)
    )
    add_memory(
        store, relation="lives_in", value="Medchal", importance=9,
        embedding=[1.0, 0.0], updated_at=datetime(2025, 1, 1)
    )
    add_memory(
        store, relation="lives_in", value="Hyderabad", importance=9,
        embedding=[1.0, 0.0], updated_at=datetime(2025, 1, 1)
    )
    add_memory(
        store, relation="lives_in", value="Delhi", importance=9,
        embedding=[1.0, 0.0], updated_at=datetime(2026, 1, 1)
    )

    results = store.semantic_search("Where do I live?", threshold=0.0)
    penalties = {
        result["memory"].value: result["conflict_penalty"]
        for result in results
    }

    assert penalties["Delhi"] == pytest.approx(0.0)
    assert penalties["Jaipur"] == pytest.approx(0.10)
    assert penalties["Medchal"] == pytest.approx(0.10)
    assert penalties["Hyderabad"] == pytest.approx(0.10)
