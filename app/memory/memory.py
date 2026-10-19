from sqlalchemy import select, desc

from app.database.database import SessionLocal
from app.database.models import Conversation
from app.settings import require_user_id


class MemoryManager:
    def __init__(self, user_id):
        self.user_id = require_user_id(user_id)
        self.session = SessionLocal()

    def _owned(self, stmt):
        require_user_id(self.user_id)
        return stmt.where(Conversation.user_id == self.user_id)

    def save_message(self, speaker, message):
        conversation = Conversation(
            speaker=speaker,
            message=message,
            user_id=self.user_id,
        )
        self.session.add(conversation)
        self._commit()
        return conversation

    def get_all_messages(self):
        stmt = self._owned(
            select(Conversation)
        ).order_by(Conversation.id)
        return self.session.execute(stmt).scalars().all()

    def get_recent_messages(self, limit=10):
        stmt = self._owned(
            select(Conversation)
        ).order_by(desc(Conversation.id)).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def search_messages(self, keyword):
        stmt = self._owned(
            select(Conversation).where(
                Conversation.message.ilike(f"%{keyword}%")
            )
        )
        return self.session.execute(stmt).scalars().all()

    def delete_all(self):
        require_user_id(self.user_id)
        query = self.session.query(Conversation).filter(
            Conversation.user_id == self.user_id
        )

        query.delete(synchronize_session=False)
        self._commit()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def close(self):
        self.session.close()
