from app.memory.memory_store import MemoryStore

store = MemoryStore()

store.save_memory(
    subject="User",
    relation="lives_in",
    value="Neemrana",
    category="PERSONAL",
    importance=8
)

store.save_memory(
    subject="User",
    relation="likes",
    value="Python",
    category="PREFERENCE",
    importance=7
)

print("\nMEMORIES\n")

for memory in store.get_all_memories():
    print(f"ID: {memory.id}")
    print(f"Subject: {memory.subject}")
    print(f"Relation: {memory.relation}")
    print(f"Value: {memory.value}")
    print(f"Category: {memory.category}")
    print(f"Importance: {memory.importance}")
    print("-" * 40)

store.close()
