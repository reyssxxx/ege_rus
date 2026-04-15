from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import MenuAction, SubcategorySelect, TaskStart


def subcategory_keyboard(task_number: int, subcategories: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for subcat in subcategories:
        buttons.append([
            InlineKeyboardButton(
                text=subcat,
                callback_data=SubcategorySelect(task=task_number, subcat=subcat).pack(),
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="🔀 Все подряд",
            callback_data=SubcategorySelect(task=task_number, subcat="").pack(),
        )
    ])
    buttons.append([
        InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="tasks").pack())
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔀 Все подряд", callback_data=MenuAction(action="all").pack())],
        [InlineKeyboardButton(text="📝 По заданиям", callback_data=MenuAction(action="tasks").pack())],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=MenuAction(action="stats").pack())],
        [InlineKeyboardButton(text="❌ Проблемные слова", callback_data=MenuAction(action="problems").pack())],
        [InlineKeyboardButton(text="🔔 Напоминания", callback_data=MenuAction(action="reminders").pack())],
        [InlineKeyboardButton(text="🏆 Лидерборд", callback_data=MenuAction(action="leaderboard").pack())],
    ])
