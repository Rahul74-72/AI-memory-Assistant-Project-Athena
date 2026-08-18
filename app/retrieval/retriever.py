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

    @staticmethod
    def _score_memory(memory, words):
        """Score a memory by matched query words, then by importance."""
        searchable_text = (
            f"{memory.subject} "
            f"{memory.relation} "
            f"{memory.value} "
            f"{memory.category}"
        ).lower()

        searchable_words = set(
            re.findall(r"\b\w+\b", searchable_text)
        )
        matched_words = sum(word in searchable_words for word in set(words))

        return matched_words, memory.importance or 0

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

            score = self._score_memory(memory, words)

            if score[0] > 0:
                results.append((score, memory))

        results.sort(key=lambda item: item[0], reverse=True)

        return [memory for _, memory in results]

    def close(self):

        self.session.close()
