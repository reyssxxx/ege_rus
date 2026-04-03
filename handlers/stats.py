import aiosqlite
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.callbacks import MenuAction
from keyboards.menu import main_menu_keyboard
from services.stats_service import format_stats_message

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: aiosqlite.Connection):
    text = await format_stats_message(db, message.from_user.id)
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(MenuAction.filter(F.action == "stats"))
async def cb_stats(callback: CallbackQuery, db: aiosqlite.Connection):
    text = await format_stats_message(db, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()
