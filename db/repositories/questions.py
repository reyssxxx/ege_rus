import json

import aiosqlite

from db.models import Question


def _row_to_question(row: aiosqlite.Row) -> Question:
    return Question(
        id=row["id"],
        task_number=row["task_number"],
        subcategory=row["subcategory"],
        word_display=row["word_display"],
        correct_answer=row["correct_answer"],
        wrong_options=json.loads(row["wrong_options"]),
        explanation=row["explanation"],
        difficulty=row["difficulty"],
    )


async def get_question_by_id(db: aiosqlite.Connection, question_id: int) -> Question | None:
    cursor = await db.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    row = await cursor.fetchone()
    return _row_to_question(row) if row else None


async def get_random_question(
    db: aiosqlite.Connection,
    task_number: int | None,
    subcategory: str | None = None,
) -> Question | None:
    """task_number=None means all tasks."""
    if task_number is None:
        cursor = await db.execute(
            "SELECT * FROM questions ORDER BY RANDOM() LIMIT 1",
        )
    elif subcategory:
        cursor = await db.execute(
            "SELECT * FROM questions WHERE task_number = ? AND subcategory = ? ORDER BY RANDOM() LIMIT 1",
            (task_number, subcategory),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM questions WHERE task_number = ? ORDER BY RANDOM() LIMIT 1",
            (task_number,),
        )
    row = await cursor.fetchone()
    return _row_to_question(row) if row else None


async def get_weighted_question(
    db: aiosqlite.Connection,
    user_id: int,
    task_number: int | None,
    subcategory: str | None = None,
    exclude_ids: list[int] | None = None,
) -> Question | None:
    """Pick a question weighted by error history. task_number=None means all tasks."""
    if task_number is None:
        task_filter = ""
        ordered_params = [user_id]
    else:
        task_filter = "AND q.task_number = ?"
        ordered_params = [user_id, task_number]

    if subcategory:
        task_filter += " AND q.subcategory = ?"
        ordered_params.append(subcategory)

    # Исключение уже отвеченных вопросов
    exclude_filter = ""
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        exclude_filter = f" AND q.id NOT IN ({placeholders})"
        ordered_params.extend(exclude_ids)

    query = f"""
        SELECT q.*,
            COALESCE(uqs.times_shown, 0) AS ts,
            COALESCE(uqs.times_correct, 0) AS tc
        FROM questions q
        LEFT JOIN user_question_stats uqs
            ON uqs.question_id = q.id AND uqs.user_id = ?
        WHERE 1=1 {task_filter} {exclude_filter}
        ORDER BY
            CASE
                WHEN uqs.times_shown IS NULL THEN 0
                WHEN uqs.times_correct = 0 THEN 1
                ELSE 2
            END,
            CASE
                WHEN uqs.times_shown > 0 THEN CAST(uqs.times_correct AS REAL) / uqs.times_shown
                ELSE 0
            END,
            RANDOM()
        LIMIT 1
    """
    cursor = await db.execute(query, ordered_params)
    row = await cursor.fetchone()
    return _row_to_question(row) if row else None


async def get_task_answer_stats(
    db: aiosqlite.Connection, user_id: int, task_number: int
) -> tuple[int, float]:
    """Return (total_answered, accuracy_pct) for this user and task."""
    cursor = await db.execute(
        """
        SELECT COUNT(*) AS total, SUM(ua.is_correct) AS correct
        FROM user_answers ua
        JOIN questions q ON q.id = ua.question_id
        WHERE ua.user_id = ? AND q.task_number = ?
        """,
        (user_id, task_number),
    )
    row = await cursor.fetchone()
    total = row["total"] or 0
    correct = row["correct"] or 0
    accuracy = round(100.0 * correct / total, 1) if total > 0 else 0.0
    return total, accuracy
