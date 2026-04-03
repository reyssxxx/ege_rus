from datetime import datetime, timezone

import aiosqlite


async def record_answer(
    db: aiosqlite.Connection,
    user_id: int,
    question_id: int,
    is_correct: bool,
):
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        "INSERT INTO user_answers (user_id, question_id, is_correct, answered_at) VALUES (?, ?, ?, ?)",
        (user_id, question_id, int(is_correct), now),
    )

    await db.execute(
        """
        INSERT INTO user_question_stats (user_id, question_id, times_shown, times_correct, last_shown)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(user_id, question_id) DO UPDATE SET
            times_shown = times_shown + 1,
            times_correct = times_correct + ?,
            last_shown = ?
        """,
        (user_id, question_id, int(is_correct), now, int(is_correct), now),
    )
