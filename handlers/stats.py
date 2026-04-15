import logging

import aiosqlite
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.users import get_problem_question_ids, get_longest_streak
from keyboards.callbacks import MenuAction, ProblemsStart
from keyboards.stats import stats_keyboard, StatsView
from services.stats_service import format_general_stats, format_category_stats
from utils.safe_edit import safe_edit_text

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


@router.callback_query(MenuAction.filter(F.action == "problems"))
async def cb_problems(callback: CallbackQuery, db: aiosqlite.Connection):
    """Показать экран проблемных слов."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    problem_ids = await get_problem_question_ids(db, callback.from_user.id)
    if not problem_ids:
        await callback.answer("Отлично! Пока нет слов с ошибками. 💪", show_alert=True)
        return

    count = len(problem_ids)
    text = (
        "❌ <b>Проблемные слова</b>\n\n"
        f"Слова, в которых была хотя бы одна ошибка: <b>{count}</b>\n\n"
        "Бот будет показывать их в первую очередь — сначала те, где точность хуже."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Начать тренировку", callback_data=ProblemsStart().pack())],
        [InlineKeyboardButton(text="« Назад", callback_data=MenuAction(action="back").pack())],
    ])
    await safe_edit_text(callback, text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(ProblemsStart.filter())
async def cb_problems_start(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """Запустить тренировку по проблемным словам."""
    from handlers.quiz import send_question

    problem_ids = await get_problem_question_ids(db, callback.from_user.id)
    if not problem_ids:
        await callback.answer("Пока нет слов с ошибками. 💪", show_alert=True)
        return

    best_streak = await get_longest_streak(db, callback.from_user.id)
    await state.update_data(
        task_number=None,
        task_numbers=None,
        problem_ids=problem_ids,
        subcategory=None,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)
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
