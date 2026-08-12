from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor
from app.retrieval.retriever import MemoryRetriever


class ChatEngine:
    def __init__(self):
        self.memory = MemoryManager()
        self.memory_store = MemoryStore()
        self.extractor = MemoryExtractor()
        self.retriever = MemoryRetriever()

    def is_memory_question(self, text):
        text = text.lower()
        keywords = ["what", "where", "who", "when", "which", "remember", "favorite"]
        return any(word in text for word in keywords)

    def generate_response(self, user_message):
        if self.is_memory_question(user_message):
            memories = self.retriever.search(user_message)
            if memories:
                answer = "I found these memories:\n\n"
                for memory in memories:
                    answer += f"- {memory.message}\n"
                return answer
            return "I couldn't find anything relevant in my memory."

        return "I'll remember that."

    def chat(self):
        print("=" * 50)
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

            self.memory.save_message("User", user)
            memory_data = self.extractor.extract(user)
            memory_action = None

            if memory_data["save"]:
                result = self.memory_store.save_memory(
                    subject=memory_data["subject"],
                    relation=memory_data["relation"],
                    value=memory_data["value"],
                    category=memory_data["category"],
                    importance=memory_data["importance"]
                )
                memory_action = result["action"]

            response = self.generate_response(user)
            self.memory.save_message("AI", response)
            print("\nAI :", response)

            if memory_action == "created":
                print("   [Memory saved]")
            elif memory_action == "duplicate":
                print("   [Duplicate memory ignored]")
            elif memory_action == "updated":
                print("   [Memory updated]")

        self.memory.close()
        self.memory_store.close()
