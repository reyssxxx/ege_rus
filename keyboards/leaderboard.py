from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import MenuAction


class LeaderboardView(CallbackData, prefix="lb"):
    view: str  # "streak" | "solved" | "accuracy"


def leaderboard_keyboard(active_view: str) -> InlineKeyboardMarkup:
    def btn(label: str, view: str) -> InlineKeyboardButton:
        style = "success" if view == active_view else None
        return InlineKeyboardButton(text=label, callback_data=LeaderboardView(view=view).pack(), style=style)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                btn("🔥 Стрик", "streak"),
                btn("✅ Решено", "solved"),
                btn("🎯 Точность", "accuracy"),
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data=MenuAction(action="back").pack())],
        ]
    )
