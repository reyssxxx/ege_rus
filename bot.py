import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_settings
from db.engine import init_db
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
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(DbSessionMiddleware(settings.db_path))
    dp.callback_query.outer_middleware(DbSessionMiddleware(settings.db_path))

    register_routers(dp)

    await init_db(settings.db_path)
    await load_questions_if_needed(settings.db_path)
    logger.info("Bot starting...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
