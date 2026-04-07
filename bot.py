import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.file_storage import StorageKey, FileStorage

from config import get_settings
from db.engine import init_db
from db.manager import DatabaseManager
from handlers import register_routers
from middlewares.db_session import DbSessionMiddleware
from services.question_loader import load_questions_if_needed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=FileStorage(path="data/fsm_state"))

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

    try:
        await dp.start_polling(bot)
    finally:
        await db_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
