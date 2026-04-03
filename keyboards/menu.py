from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import MenuAction


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔀 Все подряд", callback_data=MenuAction(action="all").pack())],
        [InlineKeyboardButton(text="📝 По заданиям", callback_data=MenuAction(action="tasks").pack())],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=MenuAction(action="stats").pack())],
    ])
