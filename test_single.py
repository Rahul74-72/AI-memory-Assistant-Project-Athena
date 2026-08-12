from app.memory.memory_store import MemoryStore

store = MemoryStore()

print("\n--- FIRST LOCATION ---")
result = store.save_memory(
    subject="User", relation="lives_in", value="Neemrana",
    category="PERSONAL", importance=8
)
print(result["action"])

print("\n--- CHANGE LOCATION ---")
result = store.save_memory(
    subject="User", relation="lives_in", value="Jaipur",
    category="PERSONAL", importance=8
)
print(result["action"])
print("Old:", result.get("old_value"))
print("New:", result["memory"].value)

print("\n--- CURRENT LOCATIONS ---")
for memory in store.get_all_memories():
    if memory.relation == "lives_in":
        print(memory.subject, "|", memory.relation, "|", memory.value)

store.close()
