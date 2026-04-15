from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import QuizAnswer, QuizControl


def answer_keyboard(question_id: int, options: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for idx, option in enumerate(options):
        buttons.append([
            InlineKeyboardButton(
                text=option,
                callback_data=QuizAnswer(qid=question_id, idx=idx).pack(),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def stop_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для кратких заданий (авто-переход) и feedback."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏹ Стоп", callback_data=QuizControl(action="stop").pack())],
    ])


def continue_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для заданий с пояснением (ручной переход)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Продолжить", callback_data=QuizControl(action="continue").pack())],
        [InlineKeyboardButton(text="⏹ Стоп",       callback_data=QuizControl(action="stop").pack())],
    ])


