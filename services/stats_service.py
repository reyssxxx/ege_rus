import aiosqlite

from db.models import UserStats, CategoryStats, ProblemWord
from db.repositories.users import get_user_stats, get_category_stats, get_problem_words
from utils.constants import TASK_NAMES


def progress_bar(correct: int, total: int, length: int = 10) -> str:
    """Создаёт прогресс-бар с процентом."""
    if total == 0:
        return "░" * length + " —"
    ratio = correct / total
    filled = round(ratio * length)
    bar = "▓" * filled + "░" * (length - filled)
    pct = round(ratio * 100)
    return f"{bar} {pct}%"


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
        f"{progress_bar(stats.correct_answers, stats.total_answers, 16)}",
        "",
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
        bar = progress_bar(data["correct"], data["total"], 10)
        lines.append(f"{emoji} <b>{task_num}. {name}</b>")
        lines.append(f"   {bar} ({data['total']} отв.)")
        lines.append("")

    return "\n".join(lines)


TASK_EMOJIS = {
    4: "🗣",
    5: "📚",
    9: "🔤",
    10: "🔡",
    11: "🔠",
    12: "✍️",
    14: "🔗",
    15: "📝",
}


async def format_problem_words(db: aiosqlite.Connection, user_id: int) -> str:
    """Форматирует список проблемных слов."""
    problems = await get_problem_words(db, user_id, limit=15)

    if not problems:
        return (
            "❌ <b>Проблемные слова</b>\n\n"
            "Отлично! У вас нет слов с точностью ниже 50%.\n"
            "Продолжайте тренировку! 💪"
        )

    lines = [
        "❌ <b>Проблемные слова</b>",
        "",
        "Слова, где точность < 50%:",
        "",
    ]

    for pw in problems:
        bar = "▓" * pw.times_correct + "░" * (pw.times_shown - pw.times_correct)
        lines.append(f"• <b>{pw.word_display}</b> → {pw.correct_answer}")
        lines.append(f"  {bar} {pw.accuracy_pct}% ({pw.times_shown} пок.)")
        lines.append("")

    return "\n".join(lines)
