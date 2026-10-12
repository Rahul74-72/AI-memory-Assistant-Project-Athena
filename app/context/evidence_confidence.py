class EvidenceConfidence:

    DIRECT_RELATIONS = {
        "lives_in",
        "current_job",
        "age",
        "born_in",
        "current_city",
        "current_country",
        "studies",
        "goal",
        "skills"
    }

    def assess(
        self,
        result,
        user_question
    ):

        if not result:

            return "insufficient"

        memory = result.get(
            "memory"
        )

        if memory is None:

            return "insufficient"

        lifecycle_state = result.get(
            "lifecycle_state",
            getattr(
                memory,
                "lifecycle_state",
                "active"
            )
        )

        is_historical = (
            not getattr(memory, "active", True)
            and lifecycle_state == "archived"
            and getattr(memory, "archive_reason", None) == "replaced"
            and getattr(memory, "valid_from", None) is not None
            and getattr(memory, "valid_to", None) is not None
        )

        if lifecycle_state == "archived" and not is_historical:
            return "insufficient"

        if not getattr(memory, "active", True) and not is_historical:
            return "insufficient"

        conflict_penalty = result.get(
            "conflict_penalty",
            0.0
        )

        if conflict_penalty > 0:

            return "conflicting"

        question = (
            user_question
            or ""
        ).lower()

        relation = (
            memory.relation
            or ""
        ).lower()

        semantic_score = result.get(
            "semantic_score",
            0.0
        )

        programming_question = (
            "programming language" in question
            or "programming languages" in question
            or "languages do i know" in question
            or "language do i know" in question
            or "do i know " in question
            or question.startswith("do i know")
        )

        favorite_question = (
            "favorite" in question
            or "favourite" in question
        )

        location_question = (
            "where do i live" in question
            or "where i live" in question
            or "where am i living" in question
        )

        if favorite_question:

            return "insufficient"

        if programming_question:

            if relation == "likes":

                if semantic_score >= 0.20:

                    return "medium"

                return "insufficient"

            return "insufficient"

        if location_question:

            if relation in {
                "lives_in",
                "current_city",
                "current_country"
            }:

                if semantic_score >= 0.20:

                    return "high"

            return "insufficient"

        if relation in self.DIRECT_RELATIONS:

            if semantic_score >= 0.20:

                return "high"

        return "insufficient"

    def find_conflicting_relations(
        self,
        memories
    ):

        single_value_relations = {
            "lives_in",
            "current_job",
            "age",
            "born_in",
            "current_city",
            "current_country"
        }

        relation_values = {}

        for result in memories:

            memory = result.get(
                "memory"
            )

            if memory is None:
                continue

            if not getattr(
                memory,
                "active",
                True
            ):
                continue

            lifecycle_state = result.get(
                "lifecycle_state",
                getattr(
                    memory,
                    "lifecycle_state",
                    "active"
                )
            )

            if lifecycle_state == "archived":
                continue

            relation = (
                memory.relation
                or ""
            ).lower()

            if relation not in single_value_relations:
                continue

            value = (
                memory.value
                or ""
            ).strip().lower()

            if relation not in relation_values:

                relation_values[
                    relation
                ] = set()

            relation_values[
                relation
            ].add(
                value
            )

        conflicting_relations = set()

        for relation, values in (
            relation_values.items()
        ):

            if len(values) > 1:

                conflicting_relations.add(
                    relation
                )

        return conflicting_relations

    def find_conflicting_historical_relations(self, memories):
        """Find historical single-value facts with overlapping validity."""
        single_value_relations = {
            "lives_in",
            "current_job",
            "age",
            "born_in",
            "current_city",
            "current_country",
        }

        historical = []

        for result in memories:
            memory = result.get("memory")
            if memory is None:
                continue

            valid_from = getattr(memory, "valid_from", None)
            valid_to = getattr(memory, "valid_to", None)

            is_historical = (
                not getattr(memory, "active", True)
                and getattr(memory, "archive_reason", None) == "replaced"
                and getattr(memory, "lifecycle_state", None) == "archived"
                and valid_from is not None
                and valid_to is not None
            )

            relation = (getattr(memory, "relation", None) or "").lower()

            if is_historical and relation in single_value_relations:
                historical.append(memory)

        conflicting = set()

        for index, first in enumerate(historical):
            for second in historical[index + 1:]:
                if first.subject != second.subject:
                    continue

                if (first.relation or "").lower() != (second.relation or "").lower():
                    continue

                if (first.value or "").strip().lower() == (second.value or "").strip().lower():
                    continue

                # Validity intervals are start-inclusive and end-exclusive.
                overlaps = (
                    first.valid_from < second.valid_to
                    and second.valid_from < first.valid_to
                )

                if overlaps:
                    conflicting.add((
                        first.subject,
                        (first.relation or "").lower(),
                    ))

        return conflicting

    def is_usable(
        self,
        confidence
    ):

        return confidence in {
            "high",
            "medium",
            "conflicting"
        }