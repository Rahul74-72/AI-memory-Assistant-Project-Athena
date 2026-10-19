
from pathlib import Path
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database.database import Base
from app.database.models import Memory
from app.memory.memory_store import MemoryStore


def test_save_memory_recovers_after_database_write_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "rollback_test.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=NullPool,
        )
        Base.metadata.create_all(bind=engine)

        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )

        store = MemoryStore.__new__(MemoryStore)
        store.user_id = 1
        store.session = session_factory()

        class Calibrator:
            def calibrate(self, relation, value, importance):
                return importance

        class Embeddings:
            def create_embedding(self, value):
                return [0.1, 0.2]

            def serialize(self, embedding):
                return "[0.1, 0.2]"

        store.importance_calibrator = Calibrator()
        store.embedding_manager = Embeddings()

        try:
            table = Memory.__tablename__

            with engine.begin() as connection:
                connection.execute(text(
                    f"""
                    CREATE TRIGGER reject_memory_insert
                    BEFORE INSERT ON "{table}"
                    BEGIN
                        SELECT RAISE(
                            ABORT, 'simulated database failure'
                        );
                    END;
                    """
                ))

            with pytest.raises(IntegrityError):
                store.save_memory(
                    "User", "likes", "Python", "preference"
                )

            # This should work without the test manually rolling back.
            assert store.session.execute(
                text("SELECT 1")
            ).scalar_one() == 1

        finally:
            store.session.close()
            engine.dispose()
