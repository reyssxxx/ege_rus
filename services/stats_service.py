import aiosqlite

from db.models import UserStats, CategoryStats
from db.repositories.users import get_user_stats, get_category_stats
from utils.constants import TASK_NAMES


TASK_EMOJIS = {
    2: "🧩",
    4: "🗣",
    5: "📚",
    9: "🔤",
    10: "🔡",
    11: "🔠",
    12: "✍️",
    14: "🔗",
    15: "📝",
}


async def format_general_stats(db: aiosqlite.Connection, user_id: int) -> str:
    """Форматирует общую статистику пользователя."""
    stats = await get_user_stats(db, user_id)

    if stats.total_answers == 0:
        return (
            "📊 <b>Ваша статистика</b>\n\n"
            "Вы ещё не ответили ни на один вопрос.\n"
            "Начни тренировку — и прогресс появится! 🚀"
        )

    lines = [
        "📊 <b>Ваша статистика</b>",
        "",
        f"📝 Всего ответов: <b>{stats.total_answers}</b>",
        f"✅ Правильных: <b>{stats.correct_answers}</b>",
        f"🎯 Точность: <b>{stats.accuracy_pct}%</b>",
        f"🏆 Лучший стрик: <b>{stats.longest_streak}</b>",
    ]

    return "\n".join(lines)


async def format_category_stats(db: aiosqlite.Connection, user_id: int) -> str:
    """Форматирует статистику по заданиям."""
    cat_stats = await get_category_stats(db, user_id)

    if not cat_stats:
        return (
            "📖 <b>Прогресс по заданиям</b>\n\n"
            "Пока нет данных. Ответь на вопросы — и здесь появится прогресс! 📝"
        )

    lines = [
        "📖 <b>Прогресс по заданиям</b>",
        "",
    ]

    # Группируем по task_number
    task_data = {}
    for cs in cat_stats:
        if cs.task_number not in task_data:
            task_data[cs.task_number] = {"total": 0, "correct": 0}
        task_data[cs.task_number]["total"] += cs.total_answers
        task_data[cs.task_number]["correct"] += cs.correct_answers

    # Сортируем по номеру задания
    for task_num in sorted(task_data.keys()):
        data = task_data[task_num]
        name = TASK_NAMES.get(task_num, f"Задание {task_num}")
        emoji = TASK_EMOJIS.get(task_num, "📝")
        total = data["total"]
        pct = round(100.0 * data["correct"] / total) if total > 0 else 0
        lines.append(f"{emoji} <b>{name}</b>  —  {pct}%  ({total} отв.)")

    return "\n".join(lines)


