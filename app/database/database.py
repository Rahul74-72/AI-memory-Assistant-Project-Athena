from pathlib import Path
from app.settings import DATA_DIR

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------------
# Database Path
# ----------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = DATA_DIR
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "memory.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ----------------------------------------
# SQLAlchemy Engine
# ----------------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False, "timeout": 30},
)


@event.listens_for(engine, "connect")
def configure_sqlite(connection, record):
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")

# ----------------------------------------
# Session Factory
# ----------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

# ----------------------------------------
# Base Class
# ----------------------------------------

Base = declarative_base()


def get_db():
    """
    Creates a new database session.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
