from typing import Any, Awaitable, Callable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            data["db"] = db
            result = await handler(event, data)
            await db.commit()
            return result
