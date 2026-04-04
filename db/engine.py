import os

import aiosqlite


async def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema_sql)
        await db.commit()

    # Миграции для существующих БД
    await _migrate_db(db_path)


async def _migrate_db(db_path: str):
    """Добавляет отсутствующие колонки."""
    async with aiosqlite.connect(db_path) as db:
        # Проверяем есть ли колонка session_streak
        try:
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "session_streak" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN session_streak INTEGER DEFAULT 0")
                await db.commit()
        except Exception:
            pass  # Таблица может быть только что создана
