from datetime import datetime


class MemoryReinforcement:

    def __init__(self):

        self.max_reinforcement = 0.25

    # =====================================================
    # CALCULATE REINFORCEMENT
    # =====================================================

    def calculate_reinforcement(
        self,
        retrieval_count,
        last_retrieved_at,
        current_time=None
    ):

        if current_time is None:

            current_time = datetime.utcnow()

        if retrieval_count <= 0:

            return 0.0

        # -----------------------------------------
        # Frequency reinforcement
        # -----------------------------------------

        frequency_bonus = (
            min(
                retrieval_count,
                10
            ) / 10
        ) * self.max_reinforcement

        # -----------------------------------------
        # Recency adjustment
        # -----------------------------------------

        recency_factor = 1.0

        if last_retrieved_at:

            age_days = (
                current_time - last_retrieved_at
            ).total_seconds() / 86400

            if age_days < 0:

                age_days = 0

            recency_factor = (
                1 / (1 + age_days)
            )

        # -----------------------------------------
        # Final reinforcement
        # -----------------------------------------

        reinforcement = (
            frequency_bonus
            * recency_factor
        )

        return max(
            0.0,
            min(
                self.max_reinforcement,
                reinforcement
            )
        )

    # =====================================================
    # RECORD RETRIEVAL
    # =====================================================

    def record_retrieval(
        self,
        memory,
        current_time=None
    ):

        if current_time is None:

            current_time = datetime.utcnow()

        memory.retrieval_count += 1

        memory.last_retrieved_at = current_time

        return memory
