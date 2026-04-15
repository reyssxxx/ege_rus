"""Сервис создания бэкапов базы данных."""

from __future__ import annotations

import os
import shutil
from datetime import datetime

import aiosqlite

from services.log_service import log_event


BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "backups")


async def create_backup(
    db: aiosqlite.Connection,
    db_path: str,
    admin_id: int | None = None,
) -> dict | None:
    """Создать бэкап БД. Возвращает информацию о бэкапе или None при ошибке."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"ege_bot_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        # WAL checkpoint перед бэкапом
        await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        await db.commit()

        shutil.copy2(db_path, backup_path)

        backup_size = os.path.getsize(backup_path)

        # Записать в лог
        await log_event(
            db, "backup",
            f"Бэкап создан: {backup_filename} ({backup_size:,} байт)",
            admin_id,
        )

        # Записать в историю бэкапов
        await db.execute(
            "INSERT INTO backups_log (backup_path, backup_size_bytes, created_by) VALUES (?, ?, ?)",
            (backup_path, backup_size, admin_id),
        )
        await db.commit()

        return {
            "path": backup_path,
            "filename": backup_filename,
            "size": backup_size,
        }

    except Exception as e:
        await log_event(
            db, "error",
            f"Ошибка создания бэкапа: {type(e).__name__}: {e}",
            admin_id,
        )
        return None


async def get_backups_list(
    db: aiosqlite.Connection,
    limit: int = 20,
) -> list[tuple[int, str, int, int | None, str]]:
    """Получить список последних бэкапов."""
    async with db.execute(
        "SELECT id, backup_path, backup_size_bytes, created_by, created_at "
        "FROM backups_log ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def delete_old_backups(
    db: aiosqlite.Connection,
    days: int = 30,
    admin_id: int | None = None,
) -> int:
    """Удалить бэкапы старше N дней. Возвращает количество удалённых."""
    cutoff_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Находим старые записи
    async with db.execute(
        "SELECT id, backup_path FROM backups_log "
        "WHERE created_at < datetime('now', '-? days')",
        (days,),
    ) as cursor:
        old_backups = await cursor.fetchall()

    deleted = 0
    for backup_id, backup_path in old_backups:
        # Удаляем файл
        if os.path.exists(backup_path):
            os.remove(backup_path)
        # Удаляем запись
        await db.execute("DELETE FROM backups_log WHERE id = ?", (backup_id,))
        deleted += 1

    if deleted > 0:
        await log_event(
            db, "backup",
            f"Удалено {deleted} старых бэкапов (старше {days} дней)",
            admin_id,
        )
        await db.commit()

    return deleted
