from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
import aiosqlite

from keyboards.leaderboard import LeaderboardView, leaderboard_keyboard
from services.leaderboard_service import format_leaderboard, get_leaderboard
from utils.safe_edit import safe_edit_text

router = Router()


async def _show_leaderboard(
    target: Message | CallbackQuery,
    db: aiosqlite.Connection,
    view: str,
    edit: bool = False,
) -> None:
    user_id = target.from_user.id
    entries, user_rank, user_score = await get_leaderboard(db, view, user_id)
    text = format_leaderboard(entries, view, user_rank, user_score)
    keyboard = leaderboard_keyboard(view)

    if edit and isinstance(target, CallbackQuery):
        await safe_edit_text(target, text, reply_markup=keyboard)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(text, reply_markup=keyboard)


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message, db: aiosqlite.Connection) -> None:
    await _show_leaderboard(message, db, "streak")


@router.callback_query(LeaderboardView.filter())
async def cb_leaderboard_view(
    callback: CallbackQuery,
    callback_data: LeaderboardView,
    db: aiosqlite.Connection,
) -> None:
    await _show_leaderboard(callback, db, callback_data.view, edit=True)
