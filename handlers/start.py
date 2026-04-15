import logging

import aiosqlite
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.users import ensure_user, get_longest_streak, get_reminder_enabled
from keyboards.callbacks import MenuAction
from keyboards.menu import main_menu_keyboard
from utils.safe_edit import safe_edit_text

router = Router()
logger = logging.getLogger(__name__)


async def _start_all_tasks(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    from handlers.quiz import send_question

    # Получаем рекорд из БД
    best_streak = await get_longest_streak(db, callback.from_user.id)

    await state.update_data(
        task_number=None,
        subcategory=None,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)

WELCOME_TEXT = (
    "👋 <b>Привет!</b>\n\n"
    "Я бот для подготовки к ЕГЭ по русскому языку.\n"
    "Выбери задание и отвечай — стрик растёт на каждом правильном ответе.\n"
    "Ошибся — начни заново.\n\n"
    "Выбери действие:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: aiosqlite.Connection):
    await state.clear()
    await ensure_user(db, message.from_user.id, message.from_user.username)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(MenuAction.filter(F.action == "all"))
async def cb_all_tasks(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    await _start_all_tasks(callback, state, db)
    await callback.answer()


@router.callback_query(MenuAction.filter(F.action == "back"))
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(callback, "Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(MenuAction.filter(F.action == "reminders"))
async def cb_reminders_screen(callback: CallbackQuery, db: aiosqlite.Connection):
    from handlers.reminders import _reminder_keyboard, _reminder_text
    enabled = await get_reminder_enabled(db, callback.from_user.id)
    await safe_edit_text(callback, _reminder_text(enabled), reply_markup=_reminder_keyboard(enabled))
    await callback.answer()


@router.callback_query(MenuAction.filter(F.action == "leaderboard"))
async def cb_leaderboard(callback: CallbackQuery, db: aiosqlite.Connection):
    from handlers.leaderboard import _show_leaderboard
    await _show_leaderboard(callback, db, "streak", edit=True)
