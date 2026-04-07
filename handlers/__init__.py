from aiogram import Dispatcher

from handlers import start, category, quiz, stats, reminders, leaderboard, admin


def register_routers(dp: Dispatcher):
    dp.include_routers(
        start.router,
        category.router,
        quiz.router,
        stats.router,
        reminders.router,
        leaderboard.router,
        admin.router,
    )
