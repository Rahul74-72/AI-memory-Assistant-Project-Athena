from app.memory.memory import MemoryManager

memory = MemoryManager()

print("\nStored Conversations:\n")
for msg in memory.get_all_messages():
    print(f"{msg.id} | {msg.speaker} | {msg.message}")

memory.close()
