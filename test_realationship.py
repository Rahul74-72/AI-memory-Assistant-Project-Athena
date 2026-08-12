from app.memory.memory_store import MemoryStore

store = MemoryStore()

print("\n--- ADD PYTHON ---")
result = store.save_memory(
    subject="User", relation="likes", value="Python",
    category="PREFERENCE", importance=7
)
print(result["action"])

print("\n--- ADD CRICKET ---")
result = store.save_memory(
    subject="User", relation="likes", value="Cricket",
    category="PREFERENCE", importance=7
)
print(result["action"])

print("\n--- ADD PYTHON AGAIN ---")
result = store.save_memory(
    subject="User", relation="likes", value="Python",
    category="PREFERENCE", importance=7
)
print(result["action"])

print("\n--- ALL MEMORIES ---")
for memory in store.get_all_memories():
    print(f"{memory.subject} | {memory.relation} | {memory.value}")

store.close()
