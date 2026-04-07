from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import MenuAction


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔀 Все подряд", callback_data=MenuAction(action="all").pack())],
        [InlineKeyboardButton(text="📝 По заданиям", callback_data=MenuAction(action="tasks").pack())],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=MenuAction(action="stats").pack())],
        [InlineKeyboardButton(text="❌ Проблемные слова", callback_data=MenuAction(action="problems").pack())],
        [InlineKeyboardButton(text="🔔 Напоминания", callback_data=MenuAction(action="reminders").pack())],
    ])
