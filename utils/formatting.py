from utils.constants import TASK_NAMES, TASK_DESCRIPTIONS

SPACER = "\u2800" * 30

TASK_PROMPTS = {
    4:  "Выберите слово с правильным ударением:",
    5:  "Выберите подходящее слово:",
    9:  "Вставьте пропущенную букву в корне:",
    10: "Вставьте пропущенную букву в приставке:",
    11: "Вставьте пропущенную букву в суффиксе:",
    12: "Вставьте пропущенную букву:",
    14: "Как пишется выделенное слово?",
    15: "Вставьте Н или НН:",
}


def _center_word(word: str) -> str:
    """Center word using invisible braille spaces."""
    # Approximate centering: SPACER is ~30 chars wide, pad word to middle
    pad = max(0, (30 - len(word)) // 2)
    return "\u2800" * pad + word


def format_question_text(
    task_number: int | None,
    subcategory: str | None,
    word_display: str,
    streak: int,
    session_total: int,
) -> str:
    prompt = TASK_PROMPTS.get(task_number, "Выберите правильный вариант:")

    # Task 5: full sentence with gap — block quote, no centering
    if task_number == 5:
        return (
            f"{SPACER}\n"
            f"{prompt}\n\n"
            f"<blockquote>{word_display}</blockquote>\n"
            f"🔥 {streak}  |  #{session_total + 1}"
        )

    centered = _center_word(word_display)
    return (
        f"{SPACER}\n"
        f"{prompt}\n\n"
        f"<b>{centered}</b>\n\n"
        f"🔥 {streak}  |  #{session_total + 1}"
    )


def format_feedback_text(
    is_correct: bool,
    word_display: str,
    correct_answer: str,
    explanation: str,
    streak: int,
    session_total: int,
) -> str:
    if is_correct:
        result = "✅ <b>Правильно!</b>"
    else:
        result = f"❌ <b>Неправильно!</b>\n\nПравильный ответ: <b>{correct_answer}</b>"

    return f"{result}\n\n💡 {explanation}\n\n🔥 {streak}  |  Вопросов: {session_total}"


def format_task_info(task_number: int, total_answered: int, accuracy: float) -> str:
    name = TASK_NAMES.get(task_number, f"Задание {task_number}")
    desc = TASK_DESCRIPTIONS.get(task_number, "")
    lines = [f"📖 <b>Задание {task_number}: {name}</b>", f"<i>{desc}</i>", ""]
    if total_answered == 0:
        lines.append("Вы ещё не отвечали на эти вопросы.")
    else:
        lines.append(f"📊 Отвечено: <b>{total_answered}</b>  |  Точность: <b>{accuracy}%</b>")
    return "\n".join(lines)


def format_session_summary(streak: int, session_total: int) -> str:
    if session_total == 0:
        return "Вы не ответили ни на один вопрос."

    lines = [
        "📋 <b>Итоги сессии</b>",
        f"{'━' * 24}",
        f"Всего вопросов: {session_total}",
        f"Лучший стрик: {streak}",
    ]

    return "\n".join(lines)
