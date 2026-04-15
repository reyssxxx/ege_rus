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

    async with db.execute(
        "SELECT COUNT(*) FROM user_answers WHERE DATE(answered_at) = DATE('now')"
    ) as cursor:
        answers_today = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) FROM questions") as cursor:
        total_questions = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "new_today": new_today,
        "inactive_7d": inactive_7d,
        "answers_today": answers_today,
        "total_questions": total_questions,
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
        f"👤 Пользователей: {stats['total_users']}\n"
        f"🆕 Новых сегодня: {stats['new_today']}\n"
        f"😴 Неактивных 7+ дней: {stats['inactive_7d']}\n"
        f"📝 Ответов сегодня: {stats['answers_today']}\n"
        f"❓ Вопросов в базе: {stats['total_questions']}"
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


async def get_error_stats(db: aiosqlite.Connection) -> list[tuple[int, str, int, int, float]]:
    """Статистика по ошибкам: задание, подкатегория, всего ответов, ошибок, процент ошибок."""
    async with db.execute(
        """
        SELECT
            q.task_number,
            COALESCE(q.subcategory, '—') as subcategory,
            COUNT(*) as total,
            SUM(CASE WHEN ua.is_correct = 0 THEN 1 ELSE 0 END) as errors,
            ROUND(100.0 * SUM(CASE WHEN ua.is_correct = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as error_pct
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        GROUP BY q.task_number, q.subcategory
        ORDER BY error_pct DESC
        """
    ) as cursor:
        return await cursor.fetchall()


def format_error_stats(rows: list[tuple[int, str, int, int, float]]) -> str:
    if not rows:
        return "❌ Статистика по ошибкам: нет данных"
    lines = ["❌ Самые сложные темы (по % ошибок):\n"]
    for task_number, subcategory, total, errors, error_pct in rows[:15]:
        name = TASK_NAMES.get(task_number, f"Задание {task_number}")
        lines.append(
            f"З{task_number} | {subcategory}: {error_pct}% ошибок "
            f"({errors}/{total})"
        )
    return "\n".join(lines)


async def get_questions_per_task(db: aiosqlite.Connection) -> list[tuple[int, int]]:
    """Количество вопросов в базе по каждому заданию."""
    async with db.execute(
        "SELECT task_number, COUNT(*) FROM questions GROUP BY task_number ORDER BY task_number"
    ) as cursor:
        return await cursor.fetchall()


def format_questions_count(rows: list[tuple[int, int]]) -> str:
    if not rows:
        return "❓ Вопросов в базе: нет данных"
    lines = ["❓ Количество вопросов по заданиям:\n"]
    for task_number, cnt in rows:
        name = TASK_NAMES.get(task_number, f"Задание {task_number}")
        lines.append(f"З{task_number} ({name}): {cnt} вопросов")
    return "\n".join(lines)


async def get_conversion_stats(db: aiosqlite.Connection) -> dict:
    """Воронка: зарегистрировались → начали → ответили 10+ → ответили 50+."""
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(DISTINCT user_id) FROM user_answers"
    ) as cursor:
        started = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT user_id, COUNT(*) as cnt FROM user_answers "
        "  GROUP BY user_id HAVING cnt >= 10"
        ")"
    ) as cursor:
        answered_10 = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT user_id, COUNT(*) as cnt FROM user_answers "
        "  GROUP BY user_id HAVING cnt >= 50"
        ")"
    ) as cursor:
        answered_50 = (await cursor.fetchone())[0]

    return {
        "total_users": total,
        "started": started,
        "answered_10": answered_10,
        "answered_50": answered_50,
    }


def format_conversion(stats: dict) -> str:
    total = stats.get("total_users", 0)
    started = stats.get("started", 0)
    a10 = stats.get("answered_10", 0)
    a50 = stats.get("answered_50", 0)

    pct_started = round(100.0 * started / total, 1) if total else 0
    pct_10 = round(100.0 * a10 / total, 1) if total else 0
    pct_50 = round(100.0 * a50 / total, 1) if total else 0

    return (
        "📈 Воронка активности:\n\n"
        f"👤 Всего пользователей: {total}\n"
        f"▶️ Начали заниматься: {started} ({pct_started}%)\n"
        f"🔟 10+ ответов: {a10} ({pct_10}%)\n"
        f"5️⃣0️⃣ 50+ ответов: {a50} ({pct_50}%)"
    )


async def get_overall_accuracy(db: aiosqlite.Connection) -> tuple[float, int, int]:
    """Общая точность ответов: процент, правильных, всего."""
    async with db.execute(
        "SELECT COUNT(*), SUM(is_correct) FROM user_answers"
    ) as cursor:
        row = await cursor.fetchone()
        total = row[0] or 0
        correct = row[1] or 0

    accuracy = round(100.0 * correct / total, 1) if total else 0
    return accuracy, correct, total
