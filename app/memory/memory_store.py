from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryStore:
    def __init__(self):
        self.session = SessionLocal()

    def save_memory(self, subject, relation, value, category, importance=5):
        single_value_relations = {
            "lives_in", "current_job", "age", "born_in",
            "current_city", "current_country"
        }

        duplicate_stmt = select(Memory).where(
            Memory.subject == subject,
            Memory.relation == relation,
            Memory.active.is_(True)
        )

        existing_memories = self.session.execute(duplicate_stmt).scalars().all()

        for memory in existing_memories:
            if memory.value.strip().lower() == value.strip().lower():
                return {"action": "duplicate", "memory": memory}

        if relation not in single_value_relations:
            memory = Memory(
                subject=subject,
                relation=relation,
                value=value,
                category=category,
                importance=importance,
                active=True
            )
            self.session.add(memory)
            self.session.commit()
            return {"action": "created", "memory": memory}

        if existing_memories:
            old_memory = existing_memories[0]
            old_value = old_memory.value
            old_memory.value = value
            old_memory.category = category
            old_memory.importance = importance
            self.session.commit()
            return {"action": "updated", "memory": old_memory, "old_value": old_value}

        memory = Memory(
            subject=subject,
            relation=relation,
            value=value,
            category=category,
            importance=importance,
            active=True
        )
        self.session.add(memory)
        self.session.commit()
        return {"action": "created", "memory": memory}

    def get_all_memories(self):
        stmt = select(Memory).where(Memory.active.is_(True)).order_by(Memory.id)
        return self.session.execute(stmt).scalars().all()

    def close(self):
        self.session.close()
