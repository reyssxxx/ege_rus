from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import StatsView


def stats_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана статистики."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Общая", callback_data=StatsView(view="general").pack()),
            InlineKeyboardButton(text="📖 По заданиям", callback_data=StatsView(view="tasks").pack()),
        ],
        [
            InlineKeyboardButton(text="❌ Проблемные", callback_data=StatsView(view="problems").pack()),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=StatsView(view="refresh").pack()),
        ],
        [
            InlineKeyboardButton(text="🏠 В меню", callback_data=StatsView(view="menu").pack()),
        ],
    ])
