from datetime import datetime, timezone, date

import aiosqlite

from db.models import UserStats, CategoryStats, ProblemWord


async def ensure_user(db: aiosqlite.Connection, user_id: int, username: str | None = None):
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """
        INSERT INTO users (user_id, username, first_seen, last_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = COALESCE(?, username),
            last_active = ?
        """,
        (user_id, username, now, now, username, now),
    )


async def update_streak(db: aiosqlite.Connection, user_id: int):
    today = date.today().isoformat()

    cursor = await db.execute(
        "SELECT current_streak, longest_streak, last_streak_date FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return

    last_date = row["last_streak_date"]
    current = row["current_streak"]
    longest = row["longest_streak"]

    if last_date == today:
        return

    yesterday = date.today().replace(day=date.today().day)  # placeholder
    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_date == yesterday:
        current += 1
    else:
        current = 1

    longest = max(longest, current)

    await db.execute(
        "UPDATE users SET current_streak = ?, longest_streak = ?, last_streak_date = ? WHERE user_id = ?",
        (current, longest, today, user_id),
    )


async def get_user_stats(db: aiosqlite.Connection, user_id: int) -> UserStats:
    cursor = await db.execute(
        """
        SELECT
            COUNT(*) AS total_answers,
            SUM(is_correct) AS correct_answers
        FROM user_answers WHERE user_id = ?
        """,
        (user_id,),
    )
    row = await cursor.fetchone()
    total = row["total_answers"] or 0
    correct = row["correct_answers"] or 0
    accuracy = round(100.0 * correct / total, 1) if total > 0 else 0.0

    cursor2 = await db.execute(
        "SELECT current_streak, longest_streak FROM users WHERE user_id = ?",
        (user_id,),
    )
    user_row = await cursor2.fetchone()

    return UserStats(
        total_answers=total,
        correct_answers=correct,
        accuracy_pct=accuracy,
        current_streak=user_row["current_streak"] if user_row else 0,
        longest_streak=user_row["longest_streak"] if user_row else 0,
    )


async def get_category_stats(db: aiosqlite.Connection, user_id: int) -> list[CategoryStats]:
    cursor = await db.execute(
        """
        SELECT task_number, subcategory, total_answers, correct_answers, accuracy_pct
        FROM user_category_stats
        WHERE user_id = ?
        ORDER BY task_number, subcategory
        """,
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [
        CategoryStats(
            task_number=r["task_number"],
            subcategory=r["subcategory"],
            total_answers=r["total_answers"],
            correct_answers=r["correct_answers"],
            accuracy_pct=r["accuracy_pct"],
        )
        for r in rows
    ]


async def get_problem_words(db: aiosqlite.Connection, user_id: int, limit: int = 20) -> list[ProblemWord]:
    cursor = await db.execute(
        """
        SELECT
            uqs.question_id,
            q.word_display,
            q.correct_answer,
            uqs.times_shown,
            uqs.times_correct,
            ROUND(100.0 * uqs.times_correct / uqs.times_shown, 1) AS accuracy_pct
        FROM user_question_stats uqs
        JOIN questions q ON q.id = uqs.question_id
        WHERE uqs.user_id = ? AND uqs.times_shown >= 2
            AND CAST(uqs.times_correct AS REAL) / uqs.times_shown < 0.5
        ORDER BY accuracy_pct ASC, uqs.times_shown DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = await cursor.fetchall()
    return [
        ProblemWord(
            question_id=r["question_id"],
            word_display=r["word_display"],
            correct_answer=r["correct_answer"],
            times_shown=r["times_shown"],
            times_correct=r["times_correct"],
            accuracy_pct=r["accuracy_pct"],
        )
        for r in rows
    ]
