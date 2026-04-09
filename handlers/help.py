from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

HELP_TEXT = (
    "📖 <b>Как работает бот</b>\n\n"
    "Выбери задание → отвечай на вопросы → бот автоматически "
    "показывает следующий вопрос.\n\n"
    "Чаще ошибаешься на слове — чаще оно будет попадаться.\n\n"
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/stats — твоя статистика\n"
    "/leaderboard — таблица лидеров\n"
    "/reminders — вкл/выкл напоминания\n"
    "/help — эта справка"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
