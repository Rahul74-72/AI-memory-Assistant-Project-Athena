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
                selected_memories
            )
        )

        context_lines = []

        for result in selected_memories:

            memory = result["memory"]

            relation = (
                memory.relation
                or ""
            ).lower()

            if relation in conflicting_relations:

                confidence = "conflicting"

            else:

                confidence = (
                    self.confidence.assess(
                        result,
                        user_question
                    )
                )

            if not self.confidence.is_usable(
                confidence
            ):

                continue

            line = (
                f"- {memory.subject} "
                f"{memory.relation.replace('_', ' ')} "
                f"{memory.value} "
                f"[evidence={confidence}]"
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