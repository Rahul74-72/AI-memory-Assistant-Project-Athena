from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryContradiction:

    def __init__(self):

        self.session = SessionLocal()

        self.single_value_relations = {

            "lives_in",

            "current_job",

            "age",

            "born_in",

            "current_city",

            "current_country"
        }

    # =====================================================
    # FIND CONTRADICTIONS
    # =====================================================

    def find_contradictions(
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

        grouped_memories = {}

        # -------------------------------------------------
        # Group memories by subject and relation
        # -------------------------------------------------

        for memory in memories:

            if (
                memory.relation
                not in self.single_value_relations
            ):

                continue

            key = (
                memory.subject,
                memory.relation
            )

            if key not in grouped_memories:

                grouped_memories[key] = []

            grouped_memories[key].append(
                memory
            )

        contradictions = []

        # -------------------------------------------------
        # Find different values
        # -------------------------------------------------

        for key, group in grouped_memories.items():

            unique_values = set()

            for memory in group:

                value = (
                    memory.value
                    .strip()
                    .lower()
                )

                unique_values.add(value)

            if len(unique_values) <= 1:
                continue

            contradictions.append({

                "subject": key[0],

                "relation": key[1],

                "memories": group,

                "values": [
                    memory.value
                    for memory in group
                ]
            })

        return contradictions

    # =====================================================
    # SELECT CURRENT MEMORY
    # =====================================================

    def select_current_memory(
        self,
        memories
    ):

        if not memories:

            return None

        current_memory = memories[0]

        for memory in memories[1:]:

            # Newer updated memory wins.

            if (
                memory.updated_at
                and current_memory.updated_at
            ):

                if (
                    memory.updated_at
                    > current_memory.updated_at
                ):

                    current_memory = memory

                    continue

            # If timestamps are unavailable or equal,
            # higher retrieval count is considered.

            if (
                memory.retrieval_count
                > current_memory.retrieval_count
            ):

                current_memory = memory

        return current_memory

    # =====================================================
    # BUILD CONTRADICTION REPORT
    # =====================================================

    def build_report(
        self,
        contradictions
    ):

        report = []

        for contradiction in contradictions:

            current_memory = (
                self.select_current_memory(
                    contradiction["memories"]
                )
            )

            report.append({

                "subject": contradiction[
                    "subject"
                ],

                "relation": contradiction[
                    "relation"
                ],

                "values": contradiction[
                    "values"
                ],

                "current_memory": current_memory,

                "memory_ids": [
                    memory.id
                    for memory in contradiction[
                        "memories"
                    ]
                ],

                "action": "review_required"
            })

        return report

    # =====================================================
    # RESOLVE CONTRADICTION
    # =====================================================

    def resolve_contradiction(
        self,
        contradiction
    ):

        memories = contradiction[
            "memories"
        ]

        if len(memories) < 2:

            return {

                "action": "skipped",

                "reason": "not_a_contradiction"
            }

        current_memory = (
            self.select_current_memory(
                memories
            )
        )

        if not current_memory:

            return {

                "action": "skipped",

                "reason": "no_current_memory"
            }

        deactivated = []

        # -------------------------------------------------
        # Deactivate outdated memories
        # -------------------------------------------------

        for memory in memories:

            if memory.id == current_memory.id:
                continue

            memory.active = False

            deactivated.append(
                memory
            )

        self.session.commit()

        return {

            "action": "resolved",

            "current_memory": current_memory,

            "deactivated": deactivated
        }

    # =====================================================
    # RESOLVE ALL CONTRADICTIONS
    # =====================================================

    def resolve_all(
        self,
        limit=100
    ):

        contradictions = (
            self.find_contradictions(
                limit=limit
            )
        )

        results = []

        for contradiction in contradictions:

            result = (
                self.resolve_contradiction(
                    contradiction
                )
            )

            results.append(
                result
            )

        return results

    # =====================================================
    # GET SUMMARY
    # =====================================================

    def summarize(
        self,
        limit=100
    ):

        contradictions = (
            self.find_contradictions(
                limit=limit
            )
        )

        report = self.build_report(
            contradictions
        )

        return {

            "contradiction_count": len(
                contradictions
            ),

            "contradictions": report
        }

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.session.close()
