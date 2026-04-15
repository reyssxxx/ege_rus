import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

from config import Settings
from keyboards.admin import AdminView, admin_back_keyboard, admin_keyboard, admin_import_keyboard, admin_backup_keyboard, admin_logs_keyboard
from keyboards.menu import main_menu_keyboard
from services.admin_service import (
    format_admin_main,
    format_by_task,
    format_top_users,
    format_error_stats,
    format_questions_count,
    format_conversion,
    get_admin_stats,
    get_today_stats,
    get_stats_by_task,
    get_top_active_users,
    get_error_stats,
    get_questions_per_task,
    get_conversion_stats,
    get_overall_accuracy,
)
from services.backup_service import create_backup, get_backups_list, delete_old_backups
from services.content_manager import get_imports_history, import_from_json_file, get_question_count_by_task
from services.log_service import get_recent_logs, get_logs_summary
from utils.safe_edit import safe_edit_text

router = Router()


class AdminStates(StatesGroup):
    waiting_for_import_filename = State()
    waiting_for_cleanup_days = State()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, db: aiosqlite.Connection, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    stats = await get_admin_stats(db)
    today = await get_today_stats(db)
    stats.update(today)
    await message.answer(format_admin_main(stats), reply_markup=admin_keyboard())


@router.callback_query(AdminView.filter())
async def cb_admin_view(
    callback: CallbackQuery,
    callback_data: AdminView,
    db: aiosqlite.Connection,
    settings: Settings,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return

    view = callback_data.view
    admin_id = callback.from_user.id

    if view == "menu":
        await safe_edit_text(callback, "Главное меню:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    if view == "back":
        stats = await get_admin_stats(db)
        today = await get_today_stats(db)
        stats.update(today)
        text = format_admin_main(stats)
        keyboard = admin_keyboard()

    elif view == "top_users":
        rows = await get_top_active_users(db)
        text = format_top_users(rows)
        keyboard = admin_back_keyboard()

    elif view == "by_task":
        rows = await get_stats_by_task(db)
        text = format_by_task(rows)
        keyboard = admin_back_keyboard()

    elif view == "errors":
        rows = await get_error_stats(db)
        text = format_error_stats(rows)
        keyboard = admin_back_keyboard()

    elif view == "questions":
        rows = await get_questions_per_task(db)
        text = format_questions_count(rows)
        keyboard = admin_back_keyboard()

    elif view == "conversion":
        stats = await get_conversion_stats(db)
        text = format_conversion(stats)
        keyboard = admin_back_keyboard()

    elif view == "accuracy":
        accuracy, correct, total = await get_overall_accuracy(db)
        text = (
            f"🎯 Общая точность ответов:\n\n"
            f"✅ Правильных: {correct:,}\n"
            f"📝 Всего ответов: {total:,}\n"
            f"📊 Точность: {accuracy}%"
        )
        keyboard = admin_back_keyboard()

    elif view == "import":
        text = "📥 Управление контентом\n\nВыберите действие:"
        keyboard = admin_import_keyboard()

    elif view == "backup":
        text = "💾 Управление бэкапами\n\nВыберите действие:"
        keyboard = admin_backup_keyboard()

    elif view == "logs":
        text = "📋 Системные логи\n\nВыберите тип логов:"
        keyboard = admin_logs_keyboard()

    elif view == "logs_backup":
        rows = await get_recent_logs(db, log_type="backup")
        text = _format_logs(rows)
        keyboard = admin_back_keyboard()

    elif view == "logs_import":
        rows = await get_recent_logs(db, log_type="content_import")
        text = _format_logs(rows)
        keyboard = admin_back_keyboard()

    elif view == "import_file":
        rows = await get_imports_history(db)
        text = _format_imports(rows)
        keyboard = admin_back_keyboard()

    elif view == "backup_create":
        db_path = settings.db_path
        result = await create_backup(db, db_path, admin_id)
        if result:
            size_mb = result["size"] / (1024 * 1024)
            text = f"✅ Бэкап создан:\n\n📁 {result['filename']}\n📦 Размер: {size_mb:.2f} МБ"
        else:
            text = "❌ Ошибка при создании бэкапа. Проверьте логи."
        keyboard = admin_back_keyboard()

    elif view == "backup_list":
        rows = await get_backups_list(db)
        text = _format_backups(rows)
        keyboard = admin_back_keyboard()

    elif view == "backup_cleanup":
        # Начинаем FSM для ввода количества дней
        await callback.message.edit_text(
            "Введите количество дней (бэкапы старше этого срока будут удалены):",
        )
        await callback.answer()
        return

    else:
        await callback.answer()
        return

    await safe_edit_text(callback, text, reply_markup=keyboard)
    await callback.answer()


@router.message(AdminStates.waiting_for_cleanup_days)
async def handle_cleanup_days(message: Message, state: FSMContext, db: aiosqlite.Connection, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return

    try:
        days = int(message.text.strip())
        if days <= 0:
            await message.answer("Введите положительное число.")
            return
    except ValueError:
        await message.answer("Введите число.")
        return

    deleted = await delete_old_backups(db, days, message.from_user.id)
    await message.answer(f"🗑 Удалено бэкапов: {deleted} (старше {days} дней)", reply_markup=admin_backup_keyboard())
    await state.clear()


def _format_logs(rows: list) -> str:
    if not rows:
        return "📋 Логи: нет данных"
    lines = ["📋 Последние логи:\n"]
    for _, log_type, message_text, admin_id, created_at in rows[:20]:
        admin_str = f" (админ {admin_id})" if admin_id else ""
        lines.append(f"[{created_at[:16]}] {log_type}{admin_str}: {message_text[:80]}")
    return "\n".join(lines)


def _format_backups(rows: list) -> str:
    if not rows:
        return "💾 Бэкапы: нет данных"
    lines = ["💾 Последние бэкапы:\n"]
    for i, (_, path, size_bytes, _, created_at) in enumerate(rows, 1):
        size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
        filename = os.path.basename(path)
        lines.append(f"{i}. {filename} — {size_mb:.2f} МБ ({created_at[:16]})")
    return "\n".join(lines)


def _format_imports(rows: list) -> str:
    if not rows:
        return "📥 Импорты: нет данных"
    lines = ["📥 История импортов:\n"]
    for _, task_number, source_file, added, updated, _, imported_at in rows:
        source = source_file or "—"
        lines.append(
            f"[{imported_at[:16]}] З{task_number} | +{added} новых, ~{updated} обновлено\n"
            f"   Файл: {source}"
        )
    return "\n".join(lines)
