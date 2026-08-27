class MemoryContextBuilder:

    def __init__(self, max_memories=5):
        self.max_memories = max_memories

    def build(self, memories):

        if not memories:
            return "No relevant memories were found."

        selected_memories = memories[:self.max_memories]

        context_lines = []

        for result in selected_memories:

            memory = result["memory"]
            score = result["score"]

            line = (
                f"- {memory.subject} "
                f"{memory.relation.replace('_', ' ')} "
                f"{memory.value}"
            )

            context_lines.append(line)

        return "\n".join(context_lines)