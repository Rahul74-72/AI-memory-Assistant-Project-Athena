import re

from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryRetriever:

    def __init__(self):

        self.session = SessionLocal()

    @staticmethod
    def _search_words(question):
        """Return meaningful words without punctuation or short tokens."""
        return [
            word
            for word in re.findall(r"\b\w+\b", question.lower())
            if len(word) >= 4
        ]

    def search(self, question):

        words = self._search_words(question)

        if not words:
            return []

        results = []

        stmt = select(Memory).where(
            Memory.active.is_(True)
        )

        memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        for memory in memories:

            searchable_text = (
                f"{memory.subject} "
                f"{memory.relation} "
                f"{memory.value} "
                f"{memory.category}"
            ).lower()

            searchable_words = set(
                re.findall(r"\b\w+\b", searchable_text)
            )

            if any(word in searchable_words for word in words):
                results.append(memory)

        return results

    def close(self):

        self.session.close()
