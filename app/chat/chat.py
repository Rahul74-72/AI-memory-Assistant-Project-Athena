from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor
from app.context.context_builder import MemoryContextBuilder
from app.llm.reasoner import AIReasoner
import re


class ChatEngine:

    def __init__(self):

        # Conversation history
        self.memory = MemoryManager()

        # Long-term structured + semantic memory
        self.memory_store = MemoryStore()

        # Extract memories from user messages
        self.extractor = MemoryExtractor()

        self.context_builder = MemoryContextBuilder(max_memories=5)

        self.reasoner = AIReasoner()

    # =====================================================
    # MEMORY QUESTION DETECTION
    # =====================================================

    def is_memory_question(self, text):

        keywords = {
            "what",
            "where",
            "who",
            "when",
            "which",
            "remember",
            "favorite",
            "like",
            "study",
            "live",
            "goal",
            "skill"
        }

        words = set(re.findall(r"\b\w+\b", text.lower()))
        return bool(words & keywords)

    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    def generate_response(self, user_message):

        if self.is_memory_question(user_message):

            results = self.memory_store.semantic_search(
                user_message,
                top_k=3,
                threshold=0.20
            )

            context = self.context_builder.build(
                results
            )

            response = self.reasoner.answer(
                user_question=user_message,
                memory_context=context
            )

            return response

        return "I'll remember that."

    # =====================================================
    # CHAT LOOP
    # =====================================================

    def chat(self):

        print("=" * 50)
        print("       PROJECT ATHENA")
        print("       AI MEMORY ASSISTANT")
        print("=" * 50)
        print("Type 'exit' to quit.")
        print()

        while True:

            user = input("You : ").strip()

            if not user:
                continue

            if user.lower() == "exit":

                print("\nGoodbye!")

                break

            # ---------------------------------------------
            # Save conversation
            # ---------------------------------------------

            self.memory.save_message(
                "User",
                user
            )

            # ---------------------------------------------
            # Extract memory
            # ---------------------------------------------

            memory_data = self.extractor.extract(
                user
            )

            memory_action = None

            # ---------------------------------------------
            # Save structured memory
            # ---------------------------------------------

            if memory_data["save"]:

                result = self.memory_store.save_memory(

                    subject=memory_data["subject"],

                    relation=memory_data["relation"],

                    value=memory_data["value"],

                    category=memory_data["category"],

                    importance=memory_data["importance"]
                )

                memory_action = result["action"]

            # ---------------------------------------------
            # Generate response
            # ---------------------------------------------

            response = self.generate_response(
                user
            )

            # ---------------------------------------------
            # Save AI response
            # ---------------------------------------------

            self.memory.save_message(
                "AI",
                response
            )

            # ---------------------------------------------
            # Display
            # ---------------------------------------------

            print("\nAI :", response)

            if memory_action == "created":

                print(
                    "   [Memory saved]"
                )

            elif memory_action == "duplicate":

                print(
                    "   [Duplicate memory ignored]"
                )

            elif memory_action == "updated":

                print(
                    "   [Memory updated]"
                )

            elif memory_action == "updated_embedding":

                print(
                    "   [Memory embedding repaired]"
                )

        # ---------------------------------------------
        # Close resources
        # ---------------------------------------------

        self.memory.close()
        self.memory_store.close()
