import logging

import aiosqlite
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.callbacks import MenuAction
from keyboards.stats import stats_keyboard, StatsView
from services.stats_service import format_general_stats, format_category_stats

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: aiosqlite.Connection):
    """По умолчанию показываем общую статистику."""
    text = await format_general_stats(db, message.from_user.id)
    await message.answer(text, reply_markup=stats_keyboard())


@router.callback_query(MenuAction.filter(F.action == "stats"))
async def cb_stats(callback: CallbackQuery, db: aiosqlite.Connection):
    """Переход из главного меню."""
    text = await format_general_stats(db, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=stats_keyboard())
    await callback.answer()


@router.callback_query(StatsView.filter(F.view == "general"))
async def cb_stats_general(callback: CallbackQuery, db: aiosqlite.Connection):
    """Показать общую статистику."""
    text = await format_general_stats(db, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=stats_keyboard())
    await callback.answer()


@router.callback_query(StatsView.filter(F.view == "tasks"))
async def cb_stats_tasks(callback: CallbackQuery, db: aiosqlite.Connection):
    """Показать статистику по заданиям."""
    text = await format_category_stats(db, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=stats_keyboard())
    await callback.answer()


@router.callback_query(StatsView.filter(F.view == "refresh"))
async def cb_stats_refresh(callback: CallbackQuery, db: aiosqlite.Connection, state: FSMContext):
    """Обновить текущий вид статистики."""
    # Определяем текущий вид по последнему сообщению
    text = await format_general_stats(db, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=stats_keyboard())
    await callback.answer("✅ Обновлено!")


@router.callback_query(StatsView.filter(F.view == "menu"))
async def cb_stats_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню."""
    from keyboards.menu import main_menu_keyboard
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
