from sqlalchemy import select

from app.embeddings.embedding_manager import EmbeddingManager
from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryConsolidation:

    def __init__(self):

        self.session = SessionLocal()

        self.embedding_manager = EmbeddingManager()

        self.similarity_threshold = 0.90

    # =====================================================
    # FIND CONSOLIDATION CANDIDATES
    # =====================================================

    def find_candidates(
        self,
        limit=100
    ):

        stmt = (
            select(Memory)
            .where(
                Memory.active.is_(True)
            )
            .order_by(
                Memory.id
            )
            .limit(limit)
        )

        memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        candidates = []

        for index, memory in enumerate(memories):

            if not memory.embedding:
                continue

            memory_embedding = (
                self.embedding_manager.deserialize(
                    memory.embedding
                )
            )

            for other_memory in memories[index + 1:]:

                if not other_memory.embedding:
                    continue

                # Same subject and relation
                # are strong consolidation candidates.

                if (
                    memory.subject
                    != other_memory.subject
                ):

                    continue

                if (
                    memory.relation
                    != other_memory.relation
                ):

                    continue

                other_embedding = (
                    self.embedding_manager.deserialize(
                        other_memory.embedding
                    )
                )

                similarity = (
                    self.embedding_manager.similarity(
                        memory_embedding,
                        other_embedding
                    )
                )

                if (
                    similarity
                    >= self.similarity_threshold
                ):

                    candidates.append({

                        "memory_a": memory,

                        "memory_b": other_memory,

                        "similarity": similarity
                    })

        return candidates

    # =====================================================
    # SELECT PRIMARY MEMORY
    # =====================================================

    def select_primary(
        self,
        memory_a,
        memory_b
    ):

        # Higher importance wins.

        if (
            memory_a.importance
            > memory_b.importance
        ):

            return memory_a

        if (
            memory_b.importance
            > memory_a.importance
        ):

            return memory_b

        # More frequently retrieved memory wins.

        if (
            memory_a.retrieval_count
            > memory_b.retrieval_count
        ):

            return memory_a

        if (
            memory_b.retrieval_count
            > memory_a.retrieval_count
        ):

            return memory_b

        # Newer memory wins when the
        # previous signals are equal.

        if (
            memory_a.updated_at
            and memory_b.updated_at
        ):

            if (
                memory_a.updated_at
                >= memory_b.updated_at
            ):

                return memory_a

            return memory_b

        return memory_a

    # =====================================================
    # BUILD CONSOLIDATION PLAN
    # =====================================================

    def build_plan(
        self,
        candidates
    ):

        plan = []

        for candidate in candidates:

            memory_a = candidate["memory_a"]

            memory_b = candidate["memory_b"]

            primary = self.select_primary(
                memory_a,
                memory_b
            )

            if primary.id == memory_a.id:

                secondary = memory_b

            else:

                secondary = memory_a

            plan.append({

                "primary": primary,

                "secondary": secondary,

                "similarity": candidate[
                    "similarity"
                ],

                "action": "candidate"
            })

        return plan

    # =====================================================
    # CONSOLIDATE TWO MEMORIES
    # =====================================================

    def consolidate(
        self,
        primary,
        secondary,
        similarity=None
    ):

        # -------------------------------------------------
        # Safety checks
        # -------------------------------------------------

        if primary.id == secondary.id:

            return {

                "action": "skipped",

                "reason": "same_memory",

                "memory": primary
            }

        if not primary.active:

            return {

                "action": "skipped",

                "reason": "primary_not_active",

                "memory": primary
            }

        if not secondary.active:

            return {

                "action": "skipped",

                "reason": "secondary_not_active",

                "memory": secondary
            }

        # -------------------------------------------------
        # Preserve retrieval history
        # -------------------------------------------------

        primary.retrieval_count = (
            primary.retrieval_count
            + secondary.retrieval_count
        )

        # Preserve the most recent retrieval.

        if secondary.last_retrieved_at:

            if (
                not primary.last_retrieved_at
                or
                secondary.last_retrieved_at
                > primary.last_retrieved_at
            ):

                primary.last_retrieved_at = (
                    secondary.last_retrieved_at
                )

        # -------------------------------------------------
        # Preserve stronger importance
        # -------------------------------------------------

        if (
            secondary.importance
            > primary.importance
        ):

            primary.importance = (
                secondary.importance
            )

        # -------------------------------------------------
        # Deactivate redundant memory
        # -------------------------------------------------

        secondary.active = False

        # Keep the database row.

        # This allows historical inspection
        # instead of permanently deleting memory.

        self.session.commit()

        return {

            "action": "consolidated",

            "primary": primary,

            "secondary": secondary,

            "similarity": similarity
        }

    # =====================================================
    # CONSOLIDATE FROM PLAN
    # =====================================================

    def consolidate_plan(
        self,
        plan
    ):

        results = []

        for item in plan:

            result = self.consolidate(

                primary=item["primary"],

                secondary=item["secondary"],

                similarity=item.get(
                    "similarity"
                )
            )

            results.append(result)

        return results

    # =====================================================
    # GET CONSOLIDATION SUMMARY
    # =====================================================

    def summarize(
        self,
        limit=100
    ):

        candidates = self.find_candidates(
            limit=limit
        )

        plan = self.build_plan(
            candidates
        )

        return {

            "memory_count": len(
                self.get_active_memories(
                    limit=limit
                )
            ),

            "candidate_count": len(
                candidates
            ),

            "candidates": plan
        }

    # =====================================================
    # GET ACTIVE MEMORIES
    # =====================================================

    def get_active_memories(
        self,
        limit=100
    ):

        stmt = (
            select(Memory)
            .where(
                Memory.active.is_(True)
            )
            .order_by(
                Memory.id
            )
            .limit(limit)
        )

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
