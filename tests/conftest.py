"""Tests must never connect to the user's real database or download AI models."""
import os
import tempfile
from pathlib import Path
import pytest

_directory = tempfile.TemporaryDirectory(prefix="athena-tests-")
os.environ["ATHENA_DATA_DIR"] = _directory.name
os.environ["ATHENA_JWT_SECRET"] = "test-only-secret-do-not-use-in-production-123456"
os.environ["ATHENA_RATE_LIMIT"] = "0"


@pytest.fixture(autouse=True)
def isolated_api_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.api import app
    from app.database.database import Base, get_db
    from app.database.models import User
    engine = create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        db.add(User(id=42, username="testuser", password_hash="unused"))
        db.commit()

    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    yield factory
    app.dependency_overrides.clear()
    engine.dispose()


def pytest_sessionfinish(session, exitstatus):
    from app.database.database import engine
    engine.dispose()
    _directory.cleanup()
