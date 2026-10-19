
from pathlib import Path
import tempfile

import pytest
from sqlalchemy import Column, Integer, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker


TransactionBase = declarative_base()


class TransactionRecord(TransactionBase):
    __tablename__ = "transaction_test_records"

    id = Column(Integer, primary_key=True)
    unique_value = Column(Integer, unique=True, nullable=False)


def test_database_session_recovers_after_constraint_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "transaction_test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        TransactionBase.metadata.create_all(bind=engine)

        TestSession = sessionmaker(bind=engine)
        session = TestSession()

        try:
            session.add(TransactionRecord(unique_value=1))
            session.commit()

            session.add(TransactionRecord(unique_value=1))

            with pytest.raises(IntegrityError):
                session.commit()

            # A real failed transaction must be rolled back.
            session.rollback()

            assert session.execute(
                text("SELECT 1")
            ).scalar_one() == 1

        finally:
            session.close()
            engine.dispose()
