from datetime import datetime


class MemoryLifecycle:

    def __init__(self):

        self.weakened_threshold = 0.35

        self.archived_threshold = 0.15

        self.minimum_retrievals_for_active = 1

    # =====================================================
    # CALCULATE LIFECYCLE STATE
    # =====================================================

    def determine_state(
        self,
        memory,
        effective_importance,
        reinforcement,
        current_time=None
    ):

        if current_time is None:
            current_time = datetime.utcnow()

        combined_strength = (
            effective_importance / 10
        ) + reinforcement

        # -----------------------------------------
        # Recently retrieved memories
        # -----------------------------------------

        if (
            memory.retrieval_count
            >= self.minimum_retrievals_for_active
        ):

            if combined_strength >= (
                self.weakened_threshold
            ):

                return "active"

        # -----------------------------------------
        # Strong memories
        # -----------------------------------------

        if combined_strength >= (
            self.weakened_threshold
        ):

            return "active"

        # -----------------------------------------
        # Weakened memories
        # -----------------------------------------

        if combined_strength >= (
            self.archived_threshold
        ):

            return "weakened"

        # -----------------------------------------
        # Archived memories
        # -----------------------------------------

        return "archived"

    # =====================================================
    # APPLY LIFECYCLE STATE
    # =====================================================

    def update_state(
        self,
        memory,
        effective_importance,
        reinforcement,
        current_time=None
    ):

        state = self.determine_state(
            memory=memory,
            effective_importance=effective_importance,
            reinforcement=reinforcement,
            current_time=current_time
        )

        memory.lifecycle_state = state

        return memory
