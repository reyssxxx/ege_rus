import aiosqlite

from db.models import UserStats, CategoryStats, ProblemWord
from db.repositories.users import get_user_stats, get_category_stats, get_problem_words
from utils.constants import TASK_NAMES

def progress_bar(correct: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "░" * length
    ratio = correct / total
    filled = round(ratio * length)
    return "▓" * filled + "░" * (length - filled)


async def format_stats_message(db: aiosqlite.Connection, user_id: int) -> str:
    stats = await get_user_stats(db, user_id)
    cat_stats = await get_category_stats(db, user_id)
    problems = await get_problem_words(db, user_id, limit=10)

    if stats.total_answers == 0:
        return "📊 <b>Статистика</b>\n\nВы ещё не ответили ни на один вопрос. Начните тренировку!"

    lines = [
        "📊 <b>Ваша статистика</b>",
        f"{'━' * 24}",
        f"Всего ответов: {stats.total_answers}",
        f"Правильных: {stats.correct_answers}",
        f"Точность: {stats.accuracy_pct}%",
        f"{progress_bar(stats.correct_answers, stats.total_answers, 15)}",
        f"🔥 Стрик: {stats.current_streak} дн. (рекорд: {stats.longest_streak})",
    ]

    if cat_stats:
        lines.append(f"\n<b>По заданиям:</b>")
        for cs in cat_stats:
            name = TASK_NAMES.get(cs.task_number, f"#{cs.task_number}")
            sub = f" ({cs.subcategory})" if cs.subcategory else ""
            bar = progress_bar(cs.correct_answers, cs.total_answers, 8)
            lines.append(f"  {name}{sub}: {cs.accuracy_pct}% ({cs.total_answers} отв.) {bar}")

    if problems:
        lines.append(f"\n<b>Проблемные слова:</b>")
        for pw in problems[:5]:
            lines.append(f"  • {pw.word_display} → {pw.correct_answer} ({pw.accuracy_pct}%)")

    return "\n".join(lines)
