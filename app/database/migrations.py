import sqlite3
import secrets

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

def migrate_multiuser_ownership(database_path=None):
    """
    Add user ownership to existing Athena data.

    Existing unowned records are assigned to a legacy account.
    Safe to rerun. Does not delete memories or conversations.
    """
    path = database_path or DATABASE_PATH

    connection = sqlite3.connect(str(path))

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")

        required_tables = {"memories", "conversations"}

        existing_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        if not required_tables.issubset(existing_tables):
            raise RuntimeError(
                "Required Athena tables are missing."
            )

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        legacy_user = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            ("__athena_legacy__",),
        ).fetchone()

        if legacy_user is None:
            # This account cannot be used to log in.
            # A real account will require a properly hashed password.
            disabled_password = (
                "!disabled-legacy-" + secrets.token_hex(32)
            )

            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                ("__athena_legacy__", disabled_password),
            )

            legacy_user_id = cursor.lastrowid
        else:
            legacy_user_id = legacy_user[0]

        for table in ("memories", "conversations"):
            columns = {
                row[1]
                for row in connection.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }

            if "user_id" not in columns:
                connection.execute(
                    f"""
                    ALTER TABLE {table}
                    ADD COLUMN user_id INTEGER
                    REFERENCES users(id)
                    """
                )

            connection.execute(
                f"""
                UPDATE {table}
                SET user_id = ?
                WHERE user_id IS NULL
                """,
                (legacy_user_id,),
            )

            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                ix_{table}_user_id
                ON {table}(user_id)
                """
            )

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if violations:
            raise RuntimeError(
                f"Foreign key violations: {violations}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
