import os

import aiosqlite


async def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema_sql)
        # WAL для конкурентных записей
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.commit()
