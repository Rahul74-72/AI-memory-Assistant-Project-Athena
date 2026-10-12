import sqlite3

from app.database.database import DATABASE_PATH


def migrate_temporal_memory(database_path=None):
    """
    Add temporal validity columns to the memories table.

    Safe to run repeatedly. Existing rows are preserved.
    Unknown historical end dates remain NULL.
    """
    path = database_path or DATABASE_PATH
    connection = sqlite3.connect(str(path))

    try:
        connection.execute("BEGIN")

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

        if not columns:
            raise RuntimeError(
                "The memories table does not exist. "
                "Create tables before running this migration."
            )

        if "valid_from" not in columns:
            connection.execute(
                "ALTER TABLE memories ADD COLUMN valid_from DATETIME"
            )

        if "valid_to" not in columns:
            connection.execute(
                "ALTER TABLE memories ADD COLUMN valid_to DATETIME"
            )

        if "archive_reason" not in columns:
            connection.execute(
                "ALTER TABLE memories ADD COLUMN archive_reason VARCHAR(30)"
            )

        connection.execute("""
            UPDATE memories
            SET valid_from = created_at
            WHERE valid_from IS NULL
              AND created_at IS NOT NULL
        """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
