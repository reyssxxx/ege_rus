from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class LeaderboardView(CallbackData, prefix="lb"):
    view: str  # "streak" | "solved" | "accuracy"


def leaderboard_keyboard(active_view: str) -> InlineKeyboardMarkup:
    def btn(label: str, view: str) -> InlineKeyboardButton:
        text = f"✅ {label}" if view == active_view else label
        return InlineKeyboardButton(text=text, callback_data=LeaderboardView(view=view).pack())

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                btn("🔥 Стрик", "streak"),
                btn("✅ Решено", "solved"),
                btn("🎯 Точность", "accuracy"),
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:back")],
        ]
    )
