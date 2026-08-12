from sqlalchemy import desc, select

from app.database.database import SessionLocal
from app.database.models import Conversation


class MemoryManager:
    """Handles all conversation memory operations."""

    def __init__(self):
        self.session = SessionLocal()

    def save_message(self, speaker: str, message: str):
        conversation = Conversation(speaker=speaker, message=message)
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def get_all_messages(self):
        stmt = select(Conversation).order_by(Conversation.id)
        return self.session.execute(stmt).scalars().all()

    def get_recent_messages(self, limit=10):
        stmt = select(Conversation).order_by(desc(Conversation.id)).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def search_messages(self, keyword: str):
        stmt = select(Conversation).where(Conversation.message.ilike(f"%{keyword}%"))
        return self.session.execute(stmt).scalars().all()

    def delete_all(self):
        self.session.query(Conversation).delete()
        self.session.commit()

    def close(self):
        self.session.close()
