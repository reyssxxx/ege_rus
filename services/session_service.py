"""Сервис для записи тренировочных сессий."""

from __future__ import annotations

import json
import aiosqlite


async def record_session(
    db: aiosqlite.Connection,
    user_id: int,
    task_numbers: list[int] | None = None,
    task_number: int | None = None,
    subcategory: str | None = None,
) -> None:
    """Записать начало тренировочной сессии."""
    tasks_json = json.dumps(task_numbers) if task_numbers else None
    await db.execute(
        "INSERT INTO sessions (user_id, task_numbers, task_number, subcategory) "
        "VALUES (?, ?, ?, ?)",
        (user_id, tasks_json, task_number, subcategory),
    )
    await db.commit()
