from __future__ import annotations
import aiosqlite
from utils.constants import TASK_NAMES


async def get_admin_stats(db: aiosqlite.Connection) -> dict:
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total_users = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM users WHERE DATE(first_seen) = DATE('now')"
    ) as cursor:
        new_today = (await cursor.fetchone())[0]

    async with db.execute(
        """
        SELECT COUNT(*) FROM users
        WHERE (last_active_date < DATE('now', '-7 days') OR last_active_date IS NULL)
          AND DATE(first_seen) < DATE('now')
        """
    ) as cursor:
        inactive_7d = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "new_today": new_today,
        "inactive_7d": inactive_7d,
    }


async def get_top_active_users(db: aiosqlite.Connection) -> list[tuple[str, int]]:
    async with db.execute(
        """
        SELECT COALESCE(u.username, 'user_' || u.user_id), COUNT(*) AS cnt
        FROM user_answers ua JOIN users u USING(user_id)
        GROUP BY u.user_id
        ORDER BY cnt DESC
        LIMIT 10
        """
    ) as cursor:
        return await cursor.fetchall()


async def get_stats_by_task(db: aiosqlite.Connection) -> list[tuple[int, int]]:
    async with db.execute(
        """
        SELECT q.task_number, COUNT(*) AS cnt
        FROM user_answers ua JOIN questions q ON ua.question_id = q.id
        GROUP BY q.task_number
        ORDER BY cnt DESC
        """
    ) as cursor:
        return await cursor.fetchall()


def format_admin_main(stats: dict) -> str:
    return (
        f"👤 Пользователей всего: {stats['total_users']}\n"
        f"🆕 Новых сегодня: {stats['new_today']}\n"
        f"😴 Неактивных 7+ дней: {stats['inactive_7d']}"
    )


def format_top_users(rows: list[tuple[str, int]]) -> str:
    if not rows:
        return "👥 Топ активных: нет данных"
    lines = ["👥 Топ активных пользователей:\n"]
    for i, (username, cnt) in enumerate(rows, 1):
        lines.append(f"{i}. {username} — {cnt} ответов")
    return "\n".join(lines)


def format_by_task(rows: list[tuple[int, int]]) -> str:
    if not rows:
        return "📊 По заданиям: нет данных"
    lines = ["📊 Активность по заданиям:\n"]
    for task_number, cnt in rows:
        name = TASK_NAMES.get(task_number, f"Задание {task_number}")
        lines.append(f"Задание {task_number} ({name}): {cnt}")
    return "\n".join(lines)
