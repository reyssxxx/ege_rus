import asyncio
import logging

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_settings
from db.engine import init_db
from db.manager import DatabaseManager
from db.migrate import run_migrations
from handlers import register_routers
from middlewares.db_session import DbSessionMiddleware
from services.question_loader import load_questions_if_needed
from services.reminder_service import start_reminder_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Запуск миграций БД
    import os
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    async with aiosqlite.connect(settings.db_path) as migration_db:
        await run_migrations(migration_db)

    # Инициализация БД (создание таблиц)
    await init_db(settings.db_path)

    # Менеджер БД с одним соединением и WAL режимом
    db_manager = DatabaseManager(settings.db_path)
    await db_manager.connect()

    dp.message.outer_middleware(DbSessionMiddleware(db_manager))
    dp.callback_query.outer_middleware(DbSessionMiddleware(db_manager))

    register_routers(dp)

    await load_questions_if_needed(settings.db_path)
    logger.info("Bot starting...")

    asyncio.create_task(start_reminder_loop(bot, settings.db_path))

    try:
        await dp.start_polling(bot)
    finally:
        await db_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
