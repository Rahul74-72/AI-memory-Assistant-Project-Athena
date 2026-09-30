from datetime import datetime


class MemoryDecay:

    def __init__(self):

        self.decay_rates = {

            "name": 0.001,

            "lives_in": 0.002,

            "current_city": 0.002,

            "current_country": 0.002,

            "current_job": 0.003,

            "goal": 0.003,

            "born_in": 0.0005,

            "studies": 0.004,

            "education": 0.004,

            "skills": 0.005,

            "likes": 0.008,

            "dislikes": 0.008,

            "hobbies": 0.010
        }

        self.default_decay_rate = 0.006

    # =====================================================
    # CALCULATE MEMORY DECAY
    # =====================================================

    def calculate_decay(
        self,
        relation,
        updated_at,
        current_time=None
    ):

        if not updated_at:

            return 1.0

        if current_time is None:

            current_time = datetime.utcnow()

        age_days = (
            current_time - updated_at
        ).total_seconds() / 86400

        if age_days < 0:

            age_days = 0

        relation = relation.strip().lower()

        decay_rate = self.decay_rates.get(
            relation,
            self.default_decay_rate
        )

        decay_factor = (
            1 / (1 + decay_rate * age_days)
        )

        return max(
            0.0,
            min(1.0, decay_factor)
        )

    # =====================================================
    # CALCULATE EFFECTIVE IMPORTANCE
    # =====================================================

    def calculate_effective_importance(
        self,
        importance,
        relation,
        updated_at,
        current_time=None
    ):

        decay_factor = self.calculate_decay(
            relation=relation,
            updated_at=updated_at,
            current_time=current_time
        )

        effective_importance = (
            importance * decay_factor
        )

        return effective_importance
