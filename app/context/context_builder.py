from app.context.evidence_confidence import (
    EvidenceConfidence
)


class MemoryContextBuilder:

    def __init__(self, max_memories=5):

        if (
            isinstance(max_memories, bool)
            or not isinstance(max_memories, int)
        ):
            raise TypeError(
                "max_memories must be an integer"
            )

        if max_memories < 0:
            raise ValueError(
                "max_memories must be non-negative"
            )

        self.max_memories = max_memories

        self.confidence = (
            EvidenceConfidence()
        )

    def build(
        self,
        memories,
        user_question
    ):

        if (
            not memories
            or self.max_memories == 0
        ):
            return (
                "No sufficient evidence "
                "was found."
            )

        selected_memories = memories[
            :self.max_memories
        ]

        conflicting_relations = (
            self.confidence.find_conflicting_relations(
                memories
            )
        )

        conflicting_historical_relations = (
            self.confidence.find_conflicting_historical_relations(
                memories
            )
        )

        context_lines = []

        for result in selected_memories:

            memory = result["memory"]

            relation = (
                memory.relation
                or ""
            ).lower()

            valid_from = getattr(
                memory,
                "valid_from",
                None
            )

            valid_to = getattr(
                memory,
                "valid_to",
                None
            )

            is_historical = (
                not getattr(memory, "active", True)
                and getattr(memory, "lifecycle_state", None) == "archived"
                and getattr(memory, "archive_reason", None) == "replaced"
                and valid_from is not None
                and valid_to is not None
            )

            if is_historical and (
                memory.subject,
                relation,
            ) in conflicting_historical_relations:
                confidence = "conflicting"

            elif is_historical:
                confidence = self.confidence.assess(
                    result,
                    user_question
                )

            elif relation in conflicting_relations:
                confidence = "conflicting"

            else:
                confidence = self.confidence.assess(
                    result,
                    user_question
                )

            if not self.confidence.is_usable(
                confidence
            ):
                continue

            if is_historical:
                validity = (
                    f"valid_from={valid_from.isoformat()}, "
                    f"valid_to={valid_to.isoformat()}"
                )
                evidence_type = "historical"

            else:
                validity = (
                    f"valid_from={valid_from.isoformat()}"
                    if valid_from is not None
                    else "validity=unknown"
                )
                evidence_type = "current"

            line = (
                f"- {memory.subject} "
                f"{memory.relation.replace('_', ' ')} "
                f"{memory.value} "
                f"[evidence={confidence}; "
                f"type={evidence_type}; {validity}]"
            )

            context_lines.append(
                line
            )

        if not context_lines:
            return (
                "No sufficient evidence "
                "was found."
            )

        return "\n".join(
            context_lines
        )