from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Text, LargeBinary
from sqlalchemy import ForeignKey, Index

from .database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

class Conversation(Base):
    """
    Stores the complete conversation history.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    speaker: Mapped[str] = mapped_column(
        String(20)
    )

    message: Mapped[str] = mapped_column(
        String(5000)
    )

    def __repr__(self):
        return (
            f"<Conversation("
            f"id={self.id}, "
            f"speaker={self.speaker})>"
        )


class Memory(Base):
    """
    Stores structured long-term memories.
    """

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(100)
    )

    relation: Mapped[str] = mapped_column(
        String(100)
    )

    value: Mapped[str] = mapped_column(
        String(5000)
    )

    category: Mapped[str] = mapped_column(
        String(50)
    )

    importance: Mapped[int] = mapped_column(
        Integer,
        default=5
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    lifecycle_state: Mapped[str] = mapped_column(
        String,
        default="active"
    )
    archive_reason: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None
    )

    embedding: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    retrieval_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    last_retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    def __repr__(self):
        return (
            f"<Memory("
            f"id={self.id}, "
            f"subject={self.subject}, "
            f"relation={self.relation}, "
            f"value={self.value})>"
        )


class ImageMemory(Base):
    __tablename__ = "image_memories"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    caption: Mapped[str] = mapped_column(Text)
    image: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TrainingExample(Base):
    __tablename__ = "training_examples"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(default=False)
    level: Mapped[str] = mapped_column(String(20), default="beginner")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class CodeDocument(Base):
    __tablename__ = "code_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class UserSecurity(Base):
    __tablename__ = "user_security"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    totp_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(default=False)
    last_totp_step: Mapped[int] = mapped_column(default=-1)
    token_version: Mapped[int] = mapped_column(default=0)
    auto_collect: Mapped[bool] = mapped_column(default=False)
