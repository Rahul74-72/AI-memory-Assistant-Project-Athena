from datetime import datetime

from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory
from app.memory.memory_reinforcement import MemoryReinforcement


class AdaptiveMemoryPrioritization:

    def __init__(self):

        self.session = SessionLocal()

        self.memory_reinforcement = (
            MemoryReinforcement()
        )

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
    # CALCULATE ADAPTIVE PRIORITY
    # =====================================================

    def calculate_priority(
        self,
        memory,
        current_time=None
    ):

        if current_time is None:

            current_time = datetime.utcnow()

        # -----------------------------------------
        # Base importance
        # -----------------------------------------

        base_importance = (
            memory.importance
            / 10
        )

        # -----------------------------------------
        # Reinforcement
        # -----------------------------------------

        reinforcement = (
            self.memory_reinforcement.calculate_reinforcement(
                retrieval_count=memory.retrieval_count,
                last_retrieved_at=memory.last_retrieved_at,
                current_time=current_time
            )
        )

        # -----------------------------------------
        # Recency
        # -----------------------------------------

        recency_score = 0.0

        if memory.updated_at:

            age_days = (
                current_time
                - memory.updated_at
            ).total_seconds() / 86400

            if age_days < 0:

                age_days = 0

            recency_score = (
                1 / (1 + age_days)
            )

        # -----------------------------------------
        # Retrieval activity
        # -----------------------------------------

        retrieval_score = min(
            memory.retrieval_count,
            10
        ) / 10

        # -----------------------------------------
        # Lifecycle adjustment
        # -----------------------------------------

        lifecycle_bonus = 0.0

        if memory.lifecycle_state == "active":

            lifecycle_bonus = 0.05

        elif memory.lifecycle_state == "weakened":

            lifecycle_bonus = -0.05

        elif memory.lifecycle_state == "archived":

            lifecycle_bonus = -0.15

        # -----------------------------------------
        # Final adaptive priority
        # -----------------------------------------

        priority = (
            (base_importance * 0.50)
            + (reinforcement * 0.20)
            + (recency_score * 0.15)
            + (retrieval_score * 0.10)
            + lifecycle_bonus
        )

        return max(
            0.0,
            priority
        )

    # =====================================================
    # PRIORITIZE MEMORIES
    # =====================================================

    def prioritize(
        self,
        limit=100
    ):

        memories = self.get_active_memories(
            limit=limit
        )

        current_time = datetime.utcnow()

        results = []

        for memory in memories:

            priority = (
                self.calculate_priority(
                    memory=memory,
                    current_time=current_time
                )
            )

            results.append({

                "memory": memory,

                "priority": priority,

                "importance":
                    memory.importance,

                "retrieval_count":
                    memory.retrieval_count,

                "reinforcement":
                    self.memory_reinforcement.calculate_reinforcement(
                        retrieval_count=(
                            memory.retrieval_count
                        ),
                        last_retrieved_at=(
                            memory.last_retrieved_at
                        ),
                        current_time=current_time
                    ),

                "lifecycle_state":
                    memory.lifecycle_state
            })

        # -----------------------------------------
        # Sort by adaptive priority
        # -----------------------------------------

        results.sort(
            key=lambda item:
                item["priority"],
            reverse=True
        )

        return results

    # =====================================================
    # GET SUMMARY
    # =====================================================

    def summarize(
        self,
        limit=100
    ):

        results = self.prioritize(
            limit=limit
        )

        summary = []

        for result in results:

            memory = result[
                "memory"
            ]

            summary.append({

                "id":
                    memory.id,

                "relation":
                    memory.relation,

                "value":
                    memory.value,

                "priority":
                    round(
                        result["priority"],
                        3
                    ),

                "importance":
                    result["importance"],

                "retrieval_count":
                    result[
                        "retrieval_count"
                    ],

                "reinforcement":
                    round(
                        result[
                            "reinforcement"
                        ],
                        3
                    ),

                "lifecycle_state":
                    result[
                        "lifecycle_state"
                    ]
            })

        return summary

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.session.close()
