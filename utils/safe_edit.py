"""Утилиты для безопасного редактирования сообщений в Telegram."""

import logging

from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def safe_edit_text(callback: CallbackQuery, text: str, reply_markup=None) -> bool:
    """Безопасное редактирование текста сообщения.
    
    Возвращает True если редактирование прошло успешно.
    """
    if not callback.message:
        await callback.answer("Сообщение недоступно. Начни заново через /menu.", show_alert=True)
        return False
    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Message content unchanged, skipping edit")
            return True
        logger.warning("Failed to edit message: %s", e)
        return False


async def safe_edit_reply_markup(callback: CallbackQuery, reply_markup) -> bool:
    """Безопасное редактирование клавиатуры сообщения.
    
    Возвращает True если редактирование прошло успешно.
    """
    if not callback.message:
        await callback.answer("Сообщение недоступно. Начни заново через /menu.", show_alert=True)
        return False
    try:
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Reply markup unchanged, skipping edit")
            return True
        logger.warning("Failed to edit reply markup: %s", e)
        return False
