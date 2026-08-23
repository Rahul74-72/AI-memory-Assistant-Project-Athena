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
        """Score a memory using field-aware relevance, then importance."""
        fields = {
            "subject": (memory.subject, 3),
            "relation": (memory.relation, 3),
            "value": (memory.value, 2),
            "category": (memory.category, 1),
        }

        field_words = {
            name: set(re.findall(r"\b\w+\b", (text or "").lower()))
            for name, (text, _) in fields.items()
        }

        matched_score = 0
        for word in set(words):
            best_weight = max(
                (
                    weight
                    for name, (_, weight) in fields.items()
                    if word in field_words[name]
                ),
                default=0,
            )
            matched_score += best_weight

        return matched_score, memory.importance or 0

    def search(self, question, limit=None):
        """Return active memories ranked by relevance, optionally capped."""
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

        ranked_memories = [memory for _, memory in results]
        return ranked_memories[:limit] if limit is not None else ranked_memories

    def close(self):

        self.session.close()
