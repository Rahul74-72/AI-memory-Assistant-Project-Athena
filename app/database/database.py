from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------------
# Database Path
# ----------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "memory.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ----------------------------------------
# SQLAlchemy Engine
# ----------------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

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