from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callbacks import TaskToggle, MultiTaskStart, TaskStart, MenuAction
from utils.constants import TASK_NAMES


def tasks_keyboard(selected: set[int] | None = None) -> InlineKeyboardMarkup:
    if selected is None:
        selected = set()
    buttons = []
    for task_num, name in TASK_NAMES.items():
        mark = "✅ " if task_num in selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}Задание {task_num}: {name}",
                callback_data=TaskToggle(task=task_num).pack(),
            )
        ])
    row = []
    if selected:
        row.append(InlineKeyboardButton(
            text=f"▶ Начать ({len(selected)})",
            callback_data=MultiTaskStart().pack(),
        ))
    row.append(InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="back").pack()))
    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_info_keyboard(task_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Начать", callback_data=TaskStart(task=task_number).pack())],
        [InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="tasks").pack())],
    ])
