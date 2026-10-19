"""Local maintenance command. Explicit owner required; no private text is logged."""
import argparse
from app.memory.memory_store import MemoryStore
from app.embeddings.memory_text import memory_to_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    store = MemoryStore(args.user_id)
    try:
        memories = store.get_all_memories()
        for memory in memories:
            text = memory_to_text(memory.subject, memory.relation, memory.value)
            memory.embedding = store.embedding_manager.serialize(
                store.embedding_manager.create_embedding(text))
        store._commit()
        print(f"Updated {len(memories)} embeddings for user {args.user_id}.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
