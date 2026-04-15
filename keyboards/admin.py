from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class AdminView(CallbackData, prefix="adm"):
    view: str  # "back" | "menu" | "top_users" | "by_task" | "errors" | "questions" | "conversion" | "accuracy" | "import" | "backup" | "logs" | "logs_backup" | "logs_import" | "backup_create" | "backup_list" | "backup_cleanup" | "import_file"


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Воронка",
                    callback_data=AdminView(view="conversion").pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Ошибки по темам",
                    callback_data=AdminView(view="errors").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Точность общая",
                    callback_data=AdminView(view="accuracy").pack(),
                ),
                InlineKeyboardButton(
                    text="❓ Вопросы в базе",
                    callback_data=AdminView(view="questions").pack(),
                ),
            ],
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
                    text="📥 Импорт",
                    callback_data=AdminView(view="import").pack(),
                ),
                InlineKeyboardButton(
                    text="💾 Бэкапы",
                    callback_data=AdminView(view="backup").pack(),
                ),
                InlineKeyboardButton(
                    text="📋 Логи",
                    callback_data=AdminView(view="logs").pack(),
                ),
            ],
            [
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
                    callback_data=AdminView(view="back").pack(),
                )
            ]
        ]
    )


def admin_import_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 История импортов",
                    callback_data=AdminView(view="import_file").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data=AdminView(view="back").pack(),
                )
            ],
        ]
    )


def admin_backup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Создать бэкап",
                    callback_data=AdminView(view="backup_create").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список бэкапов",
                    callback_data=AdminView(view="backup_list").pack(),
                ),
                InlineKeyboardButton(
                    text="🗑 Очистить старые",
                    callback_data=AdminView(view="backup_cleanup").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data=AdminView(view="back").pack(),
                )
            ],
        ]
    )


def admin_logs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Все логи",
                    callback_data=AdminView(view="logs").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💾 Бэкапы",
                    callback_data=AdminView(view="logs_backup").pack(),
                ),
                InlineKeyboardButton(
                    text="📥 Импорты",
                    callback_data=AdminView(view="logs_import").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="« Назад",
                    callback_data=AdminView(view="back").pack(),
                )
            ],
        ]
    )
