import aiosqlite
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.users import ensure_user
from keyboards.callbacks import MenuAction
from keyboards.menu import main_menu_keyboard

router = Router()


async def _start_all_tasks(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    from handlers.quiz import send_question
    await state.update_data(
        task_number=None,
        subcategory=None,
        session_correct=0,
        session_total=0,
        streak=0,
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
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
