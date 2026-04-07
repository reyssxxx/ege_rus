from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
import aiosqlite

from keyboards.callbacks import ReminderToggle
from db.repositories.users import get_reminder_enabled, toggle_reminder

router = Router()


def _reminder_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    label = "🔕 Выключить" if enabled else "🔔 Включить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=ReminderToggle().pack())],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:back")],
        ]
    )


def _reminder_text(enabled: bool) -> str:
    status = "включены 🔔" if enabled else "выключены 🔕"
    return f"Напоминания: {status}\n\nЕсли ты не тренировался сегодня, бот напомнит тебе в 18:00 UTC."


@router.message(Command("reminders"))
async def cmd_reminders(message: Message, db: aiosqlite.Connection) -> None:
    enabled = await get_reminder_enabled(db, message.from_user.id)
    await message.answer(_reminder_text(enabled), reply_markup=_reminder_keyboard(enabled))


@router.callback_query(ReminderToggle.filter())
async def cb_toggle_reminder(callback: CallbackQuery, db: aiosqlite.Connection) -> None:
    new_val = await toggle_reminder(db, callback.from_user.id)
    await callback.message.edit_text(
        _reminder_text(new_val), reply_markup=_reminder_keyboard(new_val)
    )
    await callback.answer()
