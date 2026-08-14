from sqlalchemy import select

from app.embeddings.embedding_manager import EmbeddingManager
from app.embeddings.memory_text import memory_to_text
from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryStore:

    def __init__(self):
        self.session = SessionLocal()
        self.embedding_manager = EmbeddingManager()

    # =====================================================
    # SAVE / UPDATE MEMORY
    # =====================================================

    def save_memory(
        self,
        subject,
        relation,
        value,
        category,
        importance=5
    ):

        single_value_relations = {
            "lives_in",
            "current_job",
            "age",
            "born_in",
            "current_city",
            "current_country"
        }

        # Create natural-language memory representation
        memory_text = memory_to_text(
            subject,
            relation,
            value
        )

        # Create embedding
        embedding = self.embedding_manager.create_embedding(
            memory_text
        )

        embedding_json = self.embedding_manager.serialize(
            embedding
        )

        # Find existing active memories
        stmt = select(Memory).where(
            Memory.subject == subject,
            Memory.relation == relation,
            Memory.active.is_(True)
        )

        existing_memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        # -------------------------------------------------
        # Duplicate
        # -------------------------------------------------

        for memory in existing_memories:

            if (
                memory.value.strip().lower()
                == value.strip().lower()
            ):

                # Repair old memories without embeddings
                if not memory.embedding:

                    memory.embedding = embedding_json

                    self.session.commit()

                    return {
                        "action": "updated_embedding",
                        "memory": memory
                    }

                return {
                    "action": "duplicate",
                    "memory": memory
                }

        # -------------------------------------------------
        # Multi-value relation
        # -------------------------------------------------

        if relation not in single_value_relations:

            memory = Memory(
                subject=subject,
                relation=relation,
                value=value,
                category=category,
                importance=importance,
                active=True,
                embedding=embedding_json
            )

            self.session.add(memory)
            self.session.commit()

            return {
                "action": "created",
                "memory": memory
            }

        # -------------------------------------------------
        # Single-value relation
        # -------------------------------------------------

        if existing_memories:

            old_memory = existing_memories[0]

            old_value = old_memory.value

            old_memory.value = value
            old_memory.category = category
            old_memory.importance = importance
            old_memory.embedding = embedding_json

            self.session.commit()

            return {
                "action": "updated",
                "memory": old_memory,
                "old_value": old_value
            }

        # -------------------------------------------------
        # New memory
        # -------------------------------------------------

        memory = Memory(
            subject=subject,
            relation=relation,
            value=value,
            category=category,
            importance=importance,
            active=True,
            embedding=embedding_json
        )

        self.session.add(memory)
        self.session.commit()

        return {
            "action": "created",
            "memory": memory
        }

    # =====================================================
    # SEMANTIC SEARCH
    # =====================================================

    def semantic_search(
        self,
        query,
        top_k=5,
        threshold=0.30
    ):

        # Convert question into embedding
        query_embedding = (
            self.embedding_manager.create_embedding(
                query
            )
        )

        # Get active memories
        stmt = select(Memory).where(
            Memory.active.is_(True)
        )

        memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        results = []

        # Compare query against memories
        for memory in memories:

            if not memory.embedding:
                continue

            memory_embedding = (
                self.embedding_manager.deserialize(
                    memory.embedding
                )
            )

            similarity = (
                self.embedding_manager.similarity(
                    query_embedding,
                    memory_embedding
                )
            )

            if similarity >= threshold:

                results.append({
                    "memory": memory,
                    "score": similarity
                })

        # Highest score first
        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:top_k]

    # =====================================================
    # GET ALL MEMORIES
    # =====================================================

    def get_all_memories(self):

        stmt = select(Memory).where(
            Memory.active.is_(True)
        ).order_by(Memory.id)

        return (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):
        self.session.close()