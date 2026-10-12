import sqlite3

import pytest

from app.database.migrations import migrate_temporal_memory


def create_legacy_database(path):
    """Create a minimal pre-temporal schema with an existing memory."""
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY,
                subject TEXT,
                relation TEXT,
                value TEXT,
                created_at DATETIME
            )
        """)
        connection.execute("""
            INSERT INTO memories
                (id, subject, relation, value, created_at)
            VALUES
                (1, 'User', 'lives_in', 'Medchal',
                 '2026-01-15 10:30:00')
        """)


def test_migration_adds_columns_and_preserves_existing_memory(tmp_path):
    database_path = tmp_path / "legacy.db"
    create_legacy_database(database_path)

    migrate_temporal_memory(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }
        row = connection.execute("""
            SELECT id, subject, relation, value, created_at,
                   valid_from, valid_to, archive_reason
            FROM memories
            WHERE id = 1
        """).fetchone()

    assert {"valid_from", "valid_to", "archive_reason"} <= columns
    assert row[:5] == (
        1,
        "User",
        "lives_in",
        "Medchal",
        "2026-01-15 10:30:00",
    )
    assert row[5] == "2026-01-15 10:30:00"
    assert row[6] is None
    assert row[7] is None


def test_migration_can_run_twice(tmp_path):
    database_path = tmp_path / "legacy.db"
    create_legacy_database(database_path)

    migrate_temporal_memory(database_path)
    migrate_temporal_memory(database_path)

    with sqlite3.connect(database_path) as connection:
        row_count = connection.execute(
            "SELECT COUNT(*) FROM memories"
        ).fetchone()[0]
        row = connection.execute("""
            SELECT valid_from, valid_to, archive_reason
            FROM memories
            WHERE id = 1
        """).fetchone()

    assert row_count == 1
    assert row == ("2026-01-15 10:30:00", None, None)


def test_migration_preserves_existing_temporal_values(tmp_path):
    database_path = tmp_path / "temporal.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY,
                created_at DATETIME,
                valid_from DATETIME,
                valid_to DATETIME,
                archive_reason VARCHAR(30)
            )
        """)
        connection.execute("""
            INSERT INTO memories
                (id, created_at, valid_from, valid_to, archive_reason)
            VALUES
                (1, '2026-01-01 00:00:00',
                 '2025-12-01 00:00:00',
                 '2026-02-01 00:00:00', 'replaced')
        """)

    migrate_temporal_memory(database_path)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute("""
            SELECT valid_from, valid_to, archive_reason
            FROM memories
            WHERE id = 1
        """).fetchone()

    assert row == (
        "2025-12-01 00:00:00",
        "2026-02-01 00:00:00",
        "replaced",
    )


def test_migration_fails_cleanly_when_memories_table_is_missing(tmp_path):
    database_path = tmp_path / "empty.db"

    with pytest.raises(RuntimeError, match="memories table does not exist"):
        migrate_temporal_memory(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """).fetchall()

    assert tables == []
