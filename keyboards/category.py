from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import TaskSelect, TaskStart, MenuAction
from utils.constants import TASK_NAMES


def tasks_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for task_num, name in TASK_NAMES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"Задание {task_num}: {name}",
                callback_data=TaskSelect(task=task_num).pack(),
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="back").pack())
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_info_keyboard(task_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Начать", callback_data=TaskStart(task=task_number).pack())],
        [InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="tasks").pack())],
    ])
