from datetime import datetime
from pathlib import Path
import tempfile

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Memory
from app.memory.memory_store import MemoryStore


def make_store(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    store = MemoryStore.__new__(MemoryStore)
    store.session = session_factory()

    class Calibrator:
        def calibrate(self, relation, value, importance):
            return importance

    class Embeddings:
        def create_embedding(self, text):
            if "where" in text.lower() or "live" in text.lower():
                return [1.0, 0.0]
            return [0.0, 1.0]

        def serialize(self, embedding):
            import json
            return json.dumps(embedding)

        def deserialize(self, embedding):
            import json
            return json.loads(embedding)

        def similarity(self, first, second):
            return sum(a * b for a, b in zip(first, second))

    store.importance_calibrator = Calibrator()
    store.embedding_manager = Embeddings()

    return engine, store


def test_historical_search_ranks_relevant_memory_first():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_store(Path(temp_dir) / "history.db")

        try:
            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=datetime(2023, 1, 1),
            )
            store.save_memory(
                "User", "studies", "Data Science", "education",
                valid_from=datetime(2023, 1, 1),
            )

            # Give the records bounded historical intervals and stored embeddings.
            memories = store.session.execute(
                select(Memory)
            ).scalars().all()

            for memory in memories:
                memory.valid_to = datetime(2024, 1, 1)

                memory.embedding = (
                    store.embedding_manager.serialize(
                        [1.0, 0.0]
                        if memory.relation == "lives_in"
                        else [0.0, 1.0]
                    )
                )

            store.session.commit()

            results = store.search_historical_memories(
                "Where did I live in 2023?",
                datetime(2023, 1, 1),
                datetime(2024, 1, 1),
                top_k=5,
                threshold=0.20,
            )

            assert results
            assert results[0]["memory"].relation == "lives_in"
            assert results[0]["semantic_score"] == pytest.approx(1.0)
            assert all(
                result["memory"].relation != "studies"
                for result in results
            )
        finally:
            store.session.close()
            engine.dispose()


def test_historical_search_returns_empty_when_nothing_is_relevant():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_store(Path(temp_dir) / "no_match.db")

        try:
            store.save_memory(
                "User", "studies", "Data Science", "education",
                valid_from=datetime(2023, 1, 1),
            )

            memory = store.session.execute(
                select(Memory)
            ).scalars().first()

            memory.embedding = (
                store.embedding_manager.serialize([0.0, 1.0])
            )
            store.session.commit()

            results = store.search_historical_memories(
                "Where did I live in 2023?",
                datetime(2023, 1, 1),
                datetime(2024, 1, 1),
                threshold=0.20,
            )

            assert results == []
        finally:
            store.session.close()
            engine.dispose()


def test_historical_search_does_not_update_retrieval_count():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_store(Path(temp_dir) / "no_side_effects.db")

        try:
            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=datetime(2023, 1, 1),
            )

            memory = store.session.execute(
                select(Memory)
            ).scalars().first()

            memory.embedding = (
                store.embedding_manager.serialize([1.0, 0.0])
            )
            original_count = memory.retrieval_count
            original_state = memory.lifecycle_state
            store.session.commit()

            store.search_historical_memories(
                "Where did I live in 2023?",
                datetime(2023, 1, 1),
                datetime(2024, 1, 1),
            )

            store.session.expire_all()
            memory = store.session.execute(
                select(Memory)
            ).scalars().first()

            assert memory.retrieval_count == original_count
            assert memory.lifecycle_state == original_state
        finally:
            store.session.close()
            engine.dispose()
