from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor


class ChatEngine:

    def __init__(self):

        # Conversation history
        self.memory = MemoryManager()

        # Long-term structured + semantic memory
        self.memory_store = MemoryStore()

        # Extract memories from user messages
        self.extractor = MemoryExtractor()

    # =====================================================
    # MEMORY QUESTION DETECTION
    # =====================================================

    def is_memory_question(self, text):

        text = text.lower()

        keywords = [
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
        ]

        return any(
            word in text
            for word in keywords
        )

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

            if results:

                best_memory = results[0]["memory"]

                relation = best_memory.relation
                value = best_memory.value

                if relation == "lives_in":
                    return (
                        f"You currently live in {value}."
                    )

                if relation == "likes":
                    return (
                        f"You like {value}."
                    )

                if relation == "loves":
                    return (
                        f"You love {value}."
                    )

                if relation == "studies":
                    return (
                        f"You study {value}."
                    )

                if relation == "goal":
                    return (
                        f"Your goal is to {value}."
                    )

                if relation == "building":
                    return (
                        f"You are building {value}."
                    )

                if relation == "current_job":
                    return (
                        f"Your current job is {value}."
                    )

                if relation == "skills":
                    return (
                        f"Your skill is {value}."
                    )

                return (
                    f"I remember: {value}."
                )

            return (
                "I couldn't find anything relevant "
                "in my memory."
            )

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