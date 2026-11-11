from app.database.models import Memory, User
from app.retrieval.retriever import MemoryRetriever


def test_search_excludes_other_users_unowned_and_inactive_memories(isolated_api_db):
    with isolated_api_db() as db:
        db.add(User(id=43, username="otheruser", password_hash="unused"))
        db.flush()
        memories = [
            Memory(
                user_id=user_id, subject="Athena", relation="is",
                value="private project", category="project", active=active,
                importance=importance,
            )
            for user_id, active, importance in [
                (42, True, 1),
                (43, True, 10),
                (None, True, 10),
                (42, False, 10),
            ]
        ]
        db.add_all(memories)
        db.commit()
        expected_id = memories[0].id

    retriever = MemoryRetriever.__new__(MemoryRetriever)
    retriever.user_id = 42
    retriever.session = isolated_api_db()
    try:
        assert [memory.id for memory in retriever.search("Athena", limit=1)] == [expected_id]
        assert [memory.id for memory in retriever.search("Athena")] == [expected_id]
    finally:
        retriever.close()
