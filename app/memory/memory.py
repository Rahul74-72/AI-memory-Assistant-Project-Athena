from sqlalchemy import select
from sqlalchemy import desc

from app.database.database import SessionLocal
from app.database.models import Conversation


class MemoryManager:
    """
    Handles all conversation memory operations.
    """

    def __init__(self):
        self.session = SessionLocal()

    def save_message(self, speaker: str, message: str):
        """
        Save a conversation message.
        """

        conversation = Conversation(
            speaker=speaker,
            message=message
        )

        self.session.add(conversation)
        self.session.commit()

        return conversation

    def get_all_messages(self):
        """
        Return every conversation.
        """

        stmt = select(Conversation).order_by(Conversation.id)

        return self.session.execute(stmt).scalars().all()

    def get_recent_messages(self, limit=10):
        """
        Return the most recent conversations.
        """

        stmt = (
            select(Conversation)
            .order_by(desc(Conversation.id))
            .limit(limit)
        )

        return self.session.execute(stmt).scalars().all()

    def search_messages(self, keyword: str):
        """
        Search messages containing a keyword.
        """

        stmt = (
            select(Conversation)
            .where(
                Conversation.message.ilike(f"%{keyword}%")
            )
        )

        return self.session.execute(stmt).scalars().all()

    def delete_all(self):
        """
        Delete every conversation.
        """

        self.session.query(Conversation).delete()
        self.session.commit()

    def close(self):
        """
        Close database connection.
        """

        self.session.close()