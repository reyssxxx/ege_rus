"""Сервис логирования действий администратора и системных событий."""

from __future__ import annotations

import aiosqlite


async def log_event(
    db: aiosqlite.Connection,
    log_type: str,
    message: str,
    admin_id: int | None = None,
) -> None:
    """Записать событие в системный лог."""
    await db.execute(
        "INSERT INTO system_logs (log_type, message, admin_id) VALUES (?, ?, ?)",
        (log_type, message, admin_id),
    )
    await db.commit()


async def get_recent_logs(
    db: aiosqlite.Connection,
    limit: int = 30,
    log_type: str | None = None,
) -> list[tuple[int, str, str, int | None, str]]:
    """Получить последние логи, опционально фильтруя по типу."""
    query = "SELECT id, log_type, message, admin_id, created_at FROM system_logs"
    params: list = []

    if log_type:
        query += " WHERE log_type = ?"
        params.append(log_type)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    async with db.execute(query, params) as cursor:
        return await cursor.fetchall()


async def get_logs_summary(db: aiosqlite.Connection) -> dict:
    """Получить сводку по логам: количество записей по типам."""
    async with db.execute(
        "SELECT log_type, COUNT(*) as cnt FROM system_logs GROUP BY log_type ORDER BY cnt DESC"
    ) as cursor:
        rows = await cursor.fetchall()

    async with db.execute("SELECT COUNT(*) FROM system_logs") as cursor:
        total = (await cursor.fetchone())[0]

    return {
        "total": total,
        "by_type": dict(rows),
    }
