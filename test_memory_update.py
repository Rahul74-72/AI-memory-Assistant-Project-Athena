from app.memory.memory_store import MemoryStore

store = MemoryStore()

print("\n--- FIRST MEMORY ---")
result = store.save_memory(
    subject="User", relation="lives_in", value="Neemrana",
    category="PERSONAL", importance=8
)
print(result["action"])

print("\n--- DUPLICATE MEMORY ---")
result = store.save_memory(
    subject="User", relation="lives_in", value="Neemrana",
    category="PERSONAL", importance=8
)
print(result["action"])

print("\n--- UPDATED MEMORY ---")
result = store.save_memory(
    subject="User", relation="lives_in", value="Jaipur",
    category="PERSONAL", importance=8
)
print(result["action"])

if "old_value" in result:
    print("Old:", result["old_value"])
    print("New:", result["memory"].value)

print("\n--- CURRENT MEMORIES ---")
for memory in store.get_all_memories():
    print(memory.subject, "|", memory.relation, "|", memory.value)

store.close()
