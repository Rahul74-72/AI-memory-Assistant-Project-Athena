from datetime import datetime
from pathlib import Path
import tempfile

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.models import Memory
from app.memory.memory_store import MemoryStore


def test_temporal_memory():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "temporal_test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=engine)

        TestSession = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

        store = MemoryStore.__new__(MemoryStore)
        store.user_id = 1
        store.session = TestSession()

        class Calibrator:
            def calibrate(self, relation, value, importance):
                return importance

        class Embeddings:
            def create_embedding(self, text):
                return [0.1, 0.2]

            def serialize(self, embedding):
                return str(embedding)

        store.importance_calibrator = Calibrator()
        store.embedding_manager = Embeddings()

        try:
            first_start = datetime(2025, 1, 1, 12, 0, 0)

            result1 = store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )
            assert result1["memory"].valid_from == first_start

            replacement_start = datetime(2025, 6, 1, 12, 0, 0)

            result2 = store.save_memory(
                "User", "lives_in", "Medchal", "location",
                valid_from=replacement_start,
            )
            assert result2["action"] == "updated"

            store.session.expire_all()

            rows = store.session.execute(
                select(Memory)
                .where(
                    Memory.subject == "User",
                    Memory.relation == "lives_in",
                )
                .order_by(Memory.id)
            ).scalars().all()

            assert len(rows) == 2
            assert rows[0].value == "Jaipur"
            assert rows[0].valid_from == first_start
            assert rows[0].valid_to == replacement_start
            assert rows[0].active is False

            assert rows[1].value == "Medchal"
            assert rows[1].valid_from == replacement_start
            assert rows[1].valid_to is None
            assert rows[1].active is True

            duplicate = store.save_memory(
                "User", "lives_in", "Medchal", "location"
            )
            assert duplicate["action"] == "duplicate"

            store.session.expire_all()

            rows = store.session.execute(
                select(Memory).where(
                    Memory.subject == "User",
                    Memory.relation == "lives_in",
                )
            ).scalars().all()
                        # Multi-value relations should remain independent.
            first_like = store.save_memory(
                "User", "likes", "Python", "preference",
                valid_from=first_start,
            )
            second_like = store.save_memory(
                "User", "likes", "Volleyball", "preference",
                valid_from=replacement_start,
            )

            assert first_like["action"] == "created"
            assert second_like["action"] == "created"

            likes = store.session.execute(
                select(Memory).where(
                    Memory.subject == "User",
                    Memory.relation == "likes",
                )
            ).scalars().all()

            assert len(likes) == 2
            assert all(memory.active for memory in likes)
            assert all(memory.valid_to is None for memory in likes)

            # Forgetting does not invent an end date.
            forgotten = store.forget_all_memories(subject="User")
            assert len(forgotten) == 3  # Medchal + two likes

            store.session.expire_all()
            likes = store.session.execute(
                select(Memory).where(
                    Memory.subject == "User",
                    Memory.relation == "likes",
                )
            ).scalars().all()

            assert all(not memory.active for memory in likes)
            assert all(memory.valid_to is None for memory in likes)

            print("PASS: multi-value memories remain independent")
            print("PASS: forgetting leaves unknown end dates unset")

            assert len(rows) == 2
            print("PASS: first fact and historical start")
            print("PASS: replacement closes previous validity")
            print("PASS: new fact remains current")
            print("PASS: duplicate does not add history")

        finally:
            store.session.close()
            engine.dispose()


import pytest
from datetime import timezone


def make_temporal_test_store(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    store = MemoryStore.__new__(MemoryStore)
    store.user_id = 1
    store.session = TestSession()

    class Calibrator:
        def calibrate(self, relation, value, importance):
            return importance

    class Embeddings:
        def create_embedding(self, text):
            return [0.1, 0.2]

        def serialize(self, embedding):
            return str(embedding)

    store.importance_calibrator = Calibrator()
    store.embedding_manager = Embeddings()

    return engine, store


def test_valid_from_rejects_non_datetime():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "invalid_type.db"
        engine, store = make_temporal_test_store(db_path)

        try:
            with pytest.raises(TypeError, match="valid_from must be a datetime"):
                store.save_memory(
                    "User", "lives_in", "Jaipur", "location",
                    valid_from="2025-01-01",
                )

            count = store.session.execute(
                select(Memory)
            ).scalars().all()

            assert count == []
            print("PASS: non-datetime valid_from rejected")
        finally:
            store.session.close()
            engine.dispose()


def test_valid_from_rejects_timezone_aware_datetime():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "aware_datetime.db"
        engine, store = make_temporal_test_store(db_path)

        try:
            aware_start = datetime(
                2025, 1, 1, 12, 0, 0,
                tzinfo=timezone.utc,
            )

            with pytest.raises(ValueError, match="timezone-naive UTC"):
                store.save_memory(
                    "User", "lives_in", "Jaipur", "location",
                    valid_from=aware_start,
                )

            assert store.session.execute(
                select(Memory)
            ).scalars().all() == []

            print("PASS: timezone-aware valid_from rejected")
        finally:
            store.session.close()
            engine.dispose()


def test_out_of_order_replacement_leaves_database_unchanged():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "out_of_order.db"
        engine, store = make_temporal_test_store(db_path)

        try:
            first_start = datetime(2025, 1, 1, 12, 0, 0)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )

            with pytest.raises(
                ValueError,
                match="cannot start before",
            ):
                store.save_memory(
                    "User", "lives_in", "Medchal", "location",
                    valid_from=datetime(2024, 12, 1, 12, 0, 0),
                )

            store.session.expire_all()

            rows = store.session.execute(
                select(Memory).where(
                    Memory.subject == "User",
                    Memory.relation == "lives_in",
                )
            ).scalars().all()

            assert len(rows) == 1
            assert rows[0].value == "Jaipur"
            assert rows[0].active is True
            assert rows[0].valid_from == first_start
            assert rows[0].valid_to is None

            print("PASS: out-of-order replacement rejected without database changes")
        finally:
            store.session.close()
            engine.dispose()

def test_validity_start_is_inclusive_and_end_is_exclusive():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "boundaries.db"
        )

        try:
            first_start = datetime(2025, 1, 1, 12, 0)
            replacement_start = datetime(2025, 6, 1, 12, 0)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )
            store.save_memory(
                "User", "lives_in", "Medchal", "location",
                valid_from=replacement_start,
            )

            at_start = store.get_memories_valid_at(
                first_start,
                relation="lives_in",
            )
            assert [m.value for m in at_start] == ["Jaipur"]

            just_before_end = store.get_memories_valid_at(
                datetime(2025, 6, 1, 11, 59, 59),
                relation="lives_in",
            )
            assert [m.value for m in just_before_end] == ["Jaipur"]

            at_end = store.get_memories_valid_at(
                replacement_start,
                relation="lives_in",
            )
            assert [m.value for m in at_end] == ["Medchal"]

            print("PASS: validity start is inclusive")
            print("PASS: validity end is exclusive")
        finally:
            store.session.close()
            engine.dispose()


def test_archived_replacement_is_retrievable_during_validity():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "archived_history.db"
        )

        try:
            first_start = datetime(2025, 1, 1, 12, 0)
            replacement_start = datetime(2025, 6, 1, 12, 0)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )
            store.save_memory(
                "User", "lives_in", "Medchal", "location",
                valid_from=replacement_start,
            )

            historical = store.get_memories_valid_at(
                datetime(2025, 3, 1, 12, 0),
                relation="lives_in",
            )

            assert len(historical) == 1
            assert historical[0].value == "Jaipur"
            assert historical[0].active is False
            assert historical[0].valid_to == replacement_start

            print("PASS: replaced memory can be retrieved historically")
        finally:
            store.session.close()
            engine.dispose()


def test_forgotten_memory_with_unknown_end_is_excluded():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "forgotten_history.db"
        )

        try:
            first_start = datetime(2025, 1, 1, 12, 0)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )

            forgotten = store.forget_all_memories(
                subject="User"
            )
            assert len(forgotten) == 1

            store.session.expire_all()

            results = store.get_memories_valid_at(
                datetime(2025, 3, 1, 12, 0),
                relation="lives_in",
            )

            assert results == []

            print("PASS: forgetting does not establish historical validity")
        finally:
            store.session.close()
            engine.dispose()


def test_query_before_validity_start_returns_no_memory():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "before_start.db"
        )

        try:
            first_start = datetime(2025, 1, 1, 12, 0)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=first_start,
            )

            results = store.get_memories_valid_at(
                datetime(2024, 12, 31, 12, 0),
                relation="lives_in",
            )

            assert results == []

            print("PASS: memory is excluded before valid_from")
        finally:
            store.session.close()
            engine.dispose()


def test_as_of_rejects_invalid_inputs():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "invalid_as_of.db"
        )

        try:
            with pytest.raises(TypeError, match="as_of must be a datetime"):
                store.get_memories_valid_at("2025-03-01")

            with pytest.raises(ValueError, match="timezone-naive UTC"):
                store.get_memories_valid_at(
                    datetime(2025, 3, 1, tzinfo=timezone.utc)
                )
        finally:
            store.session.close()
            engine.dispose()


def test_historical_retrieval_filters_by_relation():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "relation_filter.db"
        )

        try:
            start = datetime(2025, 1, 1)

            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=start,
            )
            store.save_memory(
                "User", "studies", "Data Science", "education",
                valid_from=start,
            )

            results = store.get_memories_valid_at(
                datetime(2025, 3, 1),
                relation="lives_in",
            )

            assert [memory.value for memory in results] == ["Jaipur"]
            assert all(memory.relation == "lives_in" for memory in results)
        finally:
            store.session.close()
            engine.dispose()

def test_forgotten_memory_with_end_date_is_excluded():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "forgotten_with_end.db"
        )

        try:
            start = datetime(2025, 1, 1)

            result = store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=start,
            )
            memory = result["memory"]

            store.forget_memory(
                subject="User",
                relation="lives_in",
                value="Jaipur",
            )

            # Simulate an archived forgotten row that has an end date.
            # Without provenance, the retrieval method must not assume
            # that the date proves a real-world replacement.
            memory.valid_to = datetime(2025, 6, 1)
            store.session.commit()

            results = store.get_memories_valid_at(
                datetime(2025, 3, 1),
                relation="lives_in",
            )

            assert results == []
        finally:
            store.session.close()
            engine.dispose()

def test_interval_retrieval_returns_overlapping_replaced_memory():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "interval_replaced.db"
        )

        try:
            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=datetime(2025, 1, 1),
            )
            store.save_memory(
                "User", "lives_in", "Medchal", "location",
                valid_from=datetime(2025, 6, 1),
            )

            results = store.get_memories_overlapping_interval(
                datetime(2025, 3, 1),
                datetime(2025, 4, 1),
                relation="lives_in",
            )

            assert [memory.value for memory in results] == ["Jaipur"]
        finally:
            store.session.close()
            engine.dispose()


def test_interval_retrieval_excludes_forgotten_memory():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "interval_forgotten.db"
        )

        try:
            store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=datetime(2025, 1, 1),
            )
            store.forget_all_memories(subject="User")

            results = store.get_memories_overlapping_interval(
                datetime(2025, 3, 1),
                datetime(2025, 4, 1),
                relation="lives_in",
            )

            assert results == []
        finally:
            store.session.close()
            engine.dispose()


def test_interval_retrieval_rejects_invalid_range():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "interval_invalid.db"
        )

        try:
            with pytest.raises(ValueError, match="start must be earlier"):
                store.get_memories_overlapping_interval(
                    datetime(2025, 4, 1),
                    datetime(2025, 3, 1),
                )
        finally:
            store.session.close()
            engine.dispose()

def test_valid_at_excludes_overlapping_active_single_value_conflicts():
    with tempfile.TemporaryDirectory() as temp_dir:
        engine, store = make_temporal_test_store(
            Path(temp_dir) / "active_conflict.db"
        )

        try:
            start = datetime(2025, 1, 1)

            first = store.save_memory(
                "User", "lives_in", "Jaipur", "location",
                valid_from=start,
            )
            second = store.save_memory(
                "User", "lives_in", "Medchal", "location",
                valid_from=start,
            )

            # Simulate inconsistent existing data: both values
            # are active for the same single-value relation.
            first_memory = first["memory"]
            second_memory = second["memory"]

            first_memory.active = True
            first_memory.lifecycle_state = "active"
            first_memory.valid_to = None
            second_memory.active = True
            second_memory.lifecycle_state = "active"
            second_memory.valid_to = None
            store.session.commit()

            results = store.get_memories_valid_at(
                datetime(2025, 3, 1),
                relation="lives_in",
            )

            assert len(results) <= 1
        finally:
            store.session.close()
            engine.dispose()

if __name__ == "__main__":
    test_temporal_memory()
