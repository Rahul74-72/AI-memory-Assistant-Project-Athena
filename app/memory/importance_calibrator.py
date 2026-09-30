class ImportanceCalibrator:

    def __init__(self):

        self.relation_importance = {

            "name": 10,

            "lives_in": 9,

            "current_city": 9,

            "current_country": 9,

            "current_job": 9,

            "goal": 9,

            "born_in": 8,

            "studies": 8,

            "education": 8,

            "skills": 7,

            "likes": 6,

            "dislikes": 6,

            "hobbies": 5
        }

    # =====================================================
    # CALIBRATE IMPORTANCE
    # =====================================================

    def calibrate(
        self,
        relation,
        value,
        importance=5
    ):

        relation = relation.strip().lower()

        # -----------------------------------------
        # Relation-based importance
        # -----------------------------------------

        relation_score = (
            self.relation_importance.get(
                relation,
                importance
            )
        )

        # -----------------------------------------
        # Keep manually supplied importance
        # for unknown relations
        # -----------------------------------------

        if relation not in self.relation_importance:

            relation_score = importance

        # -----------------------------------------
        # Clamp importance
        # -----------------------------------------

        relation_score = max(
            1,
            min(10, relation_score)
        )

        return relation_score
