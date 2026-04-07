from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class AdminView(CallbackData, prefix="adm"):
    view: str  # "main" | "top_users" | "by_task" | "menu"


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Топ активных",
                    callback_data=AdminView(view="top_users").pack(),
                ),
                InlineKeyboardButton(
                    text="📊 По заданиям",
                    callback_data=AdminView(view="by_task").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=AdminView(view="main").pack(),
                ),
                InlineKeyboardButton(
                    text="🏠 В меню",
                    callback_data=AdminView(view="menu").pack(),
                ),
            ],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data=AdminView(view="main").pack(),
                )
            ]
        ]
    )
