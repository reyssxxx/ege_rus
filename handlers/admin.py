from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
import aiosqlite

from config import Settings
from keyboards.admin import AdminView, admin_back_keyboard, admin_keyboard
from services.admin_service import (
    format_admin_main,
    format_by_task,
    format_top_users,
    get_admin_stats,
    get_stats_by_task,
    get_top_active_users,
)
from utils.safe_edit import safe_edit_text

router = Router()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, db: aiosqlite.Connection, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    stats = await get_admin_stats(db)
    await message.answer(format_admin_main(stats), reply_markup=admin_keyboard())


@router.callback_query(AdminView.filter())
async def cb_admin_view(
    callback: CallbackQuery,
    callback_data: AdminView,
    db: aiosqlite.Connection,
    settings: Settings,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    view = callback_data.view

    if view == "menu":
        from keyboards.menu import main_menu_keyboard
        await safe_edit_text(callback, "Главное меню:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    if view == "main":
        stats = await get_admin_stats(db)
        text = format_admin_main(stats)
        keyboard = admin_keyboard()
    elif view == "top_users":
        rows = await get_top_active_users(db)
        text = format_top_users(rows)
        keyboard = admin_back_keyboard()
    elif view == "by_task":
        rows = await get_stats_by_task(db)
        text = format_by_task(rows)
        keyboard = admin_back_keyboard()
    else:
        await callback.answer()
        return

    await safe_edit_text(callback, text, reply_markup=keyboard)
    await callback.answer()
