from app.memory.memory_store import MemoryStore
from app.embeddings.memory_text import memory_to_text


store = MemoryStore()

memories = store.get_all_memories()

updated = 0

print("\nRegenerating embeddings...\n")

for memory in memories:

    memory_text = memory_to_text(
        memory.subject,
        memory.relation,
        memory.value
    )

    print(
        f"ID {memory.id}: {memory_text}"
    )

    embedding = (
        store.embedding_manager.create_embedding(
            memory_text
        )
    )

    memory.embedding = (
        store.embedding_manager.serialize(
            embedding
        )
    )

    updated += 1


store.session.commit()

print("\n--------------------------------")
print(f"Updated embeddings: {updated}")
print("--------------------------------")

store.close()