from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Conversation(Base):
    """Stores the complete conversation history."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    speaker: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(5000))

    def __repr__(self):
        return f"<Conversation(id={self.id}, speaker={self.speaker})>"


class Memory(Base):
    """Stores structured long-term memories."""

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100))
    relation: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(5000))
    category: Mapped[str] = mapped_column(String(50))
    importance: Mapped[int] = mapped_column(Integer, default=5)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Memory(id={self.id}, subject={self.subject}, relation={self.relation}, value={self.value})>"
