from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryRetriever:

    def __init__(self):

        self.session = SessionLocal()

    def search(self, question):

        words = question.lower().split()

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
                f"{memory.relation} "
                f"{memory.value} "
                f"{memory.category}"
            ).lower()

            for word in words:

                if len(word) < 4:
                    continue

                if word in searchable_text:

                    if memory not in results:

                        results.append(memory)

                    break

        return results

    def close(self):

        self.session.close()