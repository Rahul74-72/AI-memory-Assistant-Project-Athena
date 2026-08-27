from app.llm.ollama_client import OllamaClient


class AIReasoner:

    def __init__(self):

        self.llm = OllamaClient()

    def answer(
        self,
        user_question,
        memory_context
    ):

        prompt = f"""
You are Project Athena, an AI memory assistant.

Use the provided memories to answer the user's question.

MEMORIES:
{memory_context}

RULES:
1. Use the memories when they are relevant.
2. Do not invent personal information.
3. Do not claim something is remembered if it is not in the memories.
4. If the memories do not contain the answer, say that you don't know.
5. Answer naturally and concisely.
6. Do not mention the memory system unless necessary.

USER QUESTION:
{user_question}

ANSWER:
"""

        return self.llm.generate(prompt)