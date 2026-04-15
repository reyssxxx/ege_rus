"""Сервис управления контентом — импорт вопросов из JSON-файлов."""

from __future__ import annotations

import json
import os
from datetime import datetime

import aiosqlite

from services.log_service import log_event


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


async def get_imports_history(
    db: aiosqlite.Connection,
    limit: int = 20,
) -> list[tuple[int, int, str | None, int, int, int | None, str]]:
    """Получить историю импортов контента."""
    async with db.execute(
        "SELECT id, task_number, source_file, questions_added, questions_updated, "
        "imported_by, imported_at FROM content_imports ORDER BY imported_at DESC LIMIT ?",
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def import_from_json_file(
    db: aiosqlite.Connection,
    filename: str,
    admin_id: int | None = None,
) -> dict:
    """Импортировать вопросы из JSON-файла.

    Формат JSON:
    {
        "task_number": 9,
        "subcategories": [
            {
                "name": "Чередующиеся корни",
                "questions": [
                    {
                        "word_display": "заг_рать",
                        "correct_answer": "а",
                        "wrong_options": ["о"],
                        "explanation": "..."
                    }
                ]
            }
        ]
    }
    """
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return {"error": f"Файл не найден: {filename}"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"error": f"Ошибка JSON: {e}"}

    task_number = data.get("task_number")
    if not task_number:
        return {"error": "Отсутствует task_number в JSON"}

    subcategories = data.get("subcategories", [])
    questions_added = 0
    questions_updated = 0

    for subcat in subcategories:
        subcat_name = subcat.get("name", "")
        questions = subcat.get("questions", [])

        for q in questions:
            word_display = q.get("word_display", "")
            correct_answer = q.get("correct_answer", "")
            wrong_options = json.dumps(q.get("wrong_options", []))
            explanation = q.get("explanation", "")
            difficulty = q.get("difficulty", 1)

            if not word_display or not correct_answer:
                continue

            # Проверяем, есть ли уже такой вопрос
            async with db.execute(
                "SELECT id FROM questions WHERE word_display = ? AND task_number = ?",
                (word_display, task_number),
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # Обновляем существующий
                await db.execute(
                    "UPDATE questions SET correct_answer = ?, wrong_options = ?, "
                    "explanation = ?, difficulty = ?, subcategory = ? WHERE id = ?",
                    (correct_answer, wrong_options, explanation, difficulty, subcat_name, existing[0]),
                )
                questions_updated += 1
            else:
                # Добавляем новый
                await db.execute(
                    "INSERT INTO questions (task_number, subcategory, word_display, "
                    "correct_answer, wrong_options, explanation, difficulty) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (task_number, subcat_name, word_display, correct_answer,
                     wrong_options, explanation, difficulty),
                )
                questions_added += 1

    await db.commit()

    # Записываем в историю импортов
    await db.execute(
        "INSERT INTO content_imports (task_number, source_file, questions_added, "
        "questions_updated, imported_by) VALUES (?, ?, ?, ?, ?)",
        (task_number, filename, questions_added, questions_updated, admin_id),
    )
    await db.commit()

    await log_event(
        db, "content_import",
        f"Импорт {filename}: +{questions_added} новых, ~{questions_updated} обновлено",
        admin_id,
    )

    return {
        "task_number": task_number,
        "added": questions_added,
        "updated": questions_updated,
    }


async def get_question_count_by_task(db: aiosqlite.Connection) -> list[tuple[int, int]]:
    """Получить количество вопросов по заданиям."""
    async with db.execute(
        "SELECT task_number, COUNT(*) FROM questions GROUP BY task_number ORDER BY task_number"
    ) as cursor:
        return await cursor.fetchall()


async def delete_questions_by_task(
    db: aiosqlite.Connection,
    task_number: int,
    admin_id: int | None = None,
) -> int:
    """Удалить все вопросы для конкретного задания. Возвращает количество удалённых."""
    async with db.execute(
        "SELECT COUNT(*) FROM questions WHERE task_number = ?", (task_number,)
    ) as cursor:
        count = (await cursor.fetchone())[0]

    await db.execute("DELETE FROM questions WHERE task_number = ?", (task_number,))
    await db.commit()

    await log_event(
        db, "content_import",
        f"Удалены все вопросы для задания {task_number} ({count} шт.)",
        admin_id,
    )

    return count
