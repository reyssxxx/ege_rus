import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiosqlite

logger = logging.getLogger(__name__)


async def send_reminders(bot: Bot, db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            """
            SELECT user_id FROM users
            WHERE reminder_enabled = 1
              AND (last_active_date IS NULL OR last_active_date < date('now'))
            """
        ) as cursor:
            rows = await cursor.fetchall()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚 Начать тренировку", callback_data="menu:all")]
            ]
        )

        for (user_id,) in rows:
            try:
                await bot.send_message(
                    user_id,
                    "📚 Привет! Ты ещё не тренировался сегодня.\nЗайди — это займёт всего 5 минут!",
                    reply_markup=keyboard,
                )
            except TelegramForbiddenError:
                await db.execute(
                    "UPDATE users SET reminder_enabled = 0 WHERE user_id = ?", (user_id,)
                )
                await db.commit()
                logger.info("Disabled reminders for blocked user %s", user_id)
            except Exception as e:
                logger.warning("Failed to send reminder to %s: %s", user_id, e)


async def start_reminder_loop(bot: Bot, db_path: str) -> None:
    """Background task. Checks once per minute, fires at 18:00 UTC daily."""
    last_sent_date = None
    while True:
        try:
            now = datetime.now(timezone.utc)
            today = now.date()
            if now.hour == 18 and last_sent_date != today:
                await send_reminders(bot, db_path)
                last_sent_date = today
        except Exception as e:
            logger.error("Reminder loop error: %s", e)
        await asyncio.sleep(60)
