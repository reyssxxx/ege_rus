import os
import sqlite3
import aiosqlite

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


async def run_migrations(db: aiosqlite.Connection) -> None:
    await db.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)"
    )
    await db.commit()

    # Migration files must use zero-padded 3-digit prefixes (e.g. 001_, 002_)
    # to ensure correct sort order. Never name files with unpadded numbers (10_ etc.)
    migration_files = sorted(
        f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")
    )

    for filename in migration_files:
        version = filename  # e.g. "001_add_reminder_enabled.sql"
        async with db.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
        ) as cursor:
            already_applied = await cursor.fetchone()

        if not already_applied:
            filepath = os.path.join(MIGRATIONS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sql = f.read()
            try:
                await db.execute(sql)
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    raise
            await db.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
            )
            await db.commit()
