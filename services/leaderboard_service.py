from __future__ import annotations
import aiosqlite
from dataclasses import dataclass


@dataclass
class LeaderboardEntry:
    rank: int
    user_id: int
    username: str
    score: float | int


async def get_leaderboard(
    db: aiosqlite.Connection,
    view: str,  # "streak" | "solved" | "accuracy"
    requesting_user_id: int,
) -> tuple[list[LeaderboardEntry], int | None, float | int | None]:
    """
    Returns (top10, user_rank, user_score).
    user_rank/user_score are None if user is in top-10 or has no data.
    """
    if view == "streak":
        sql_top = """
            SELECT user_id, COALESCE(username, 'user_' || user_id), longest_streak
            FROM users
            ORDER BY longest_streak DESC
            LIMIT 10
        """
        sql_rank = """
            SELECT COUNT(*) + 1 FROM users
            WHERE longest_streak > (SELECT longest_streak FROM users WHERE user_id = ?)
        """
        sql_score = "SELECT longest_streak FROM users WHERE user_id = ?"
    elif view == "solved":
        sql_top = """
            SELECT u.user_id, COALESCE(u.username, 'user_' || u.user_id), COUNT(*) AS score
            FROM user_answers ua JOIN users u USING(user_id)
            WHERE ua.is_correct = 1
            GROUP BY u.user_id
            ORDER BY score DESC
            LIMIT 10
        """
        sql_rank = """
            SELECT COUNT(*) + 1 FROM (
                SELECT user_id, COUNT(*) AS score FROM user_answers WHERE is_correct = 1 GROUP BY user_id
            ) WHERE score > (
                SELECT COUNT(*) FROM user_answers WHERE user_id = ? AND is_correct = 1
            )
        """
        sql_score = "SELECT COUNT(*) FROM user_answers WHERE user_id = ? AND is_correct = 1"
    else:  # accuracy, min 20 answers
        sql_top = """
            SELECT u.user_id, COALESCE(u.username, 'user_' || u.user_id),
                   ROUND(100.0 * SUM(ua.is_correct) / COUNT(*), 1) AS score
            FROM user_answers ua JOIN users u USING(user_id)
            GROUP BY u.user_id
            HAVING COUNT(*) >= 20
            ORDER BY score DESC
            LIMIT 10
        """
        sql_rank = """
            SELECT COUNT(*) + 1 FROM (
                SELECT user_id, ROUND(100.0 * SUM(is_correct) / COUNT(*), 1) AS score
                FROM user_answers GROUP BY user_id HAVING COUNT(*) >= 20
            ) WHERE score > (
                SELECT ROUND(100.0 * SUM(is_correct) / COUNT(*), 1)
                FROM user_answers WHERE user_id = ? HAVING COUNT(*) >= 20
            )
        """
        sql_score = """
            SELECT ROUND(100.0 * SUM(is_correct) / COUNT(*), 1)
            FROM user_answers WHERE user_id = ? HAVING COUNT(*) >= 20
        """

    async with db.execute(sql_top) as cursor:
        rows = await cursor.fetchall()

    entries = [
        LeaderboardEntry(rank=i + 1, user_id=r[0], username=r[1], score=r[2])
        for i, r in enumerate(rows)
    ]

    # Check if requesting user is already in top-10
    user_in_top = any(e.user_id == requesting_user_id for e in entries)
    user_rank = None
    user_score = None

    if not user_in_top:
        async with db.execute(sql_score, (requesting_user_id,)) as cursor:
            score_row = await cursor.fetchone()
        if score_row and score_row[0] is not None:
            user_score = score_row[0]
            async with db.execute(sql_rank, (requesting_user_id,)) as cursor:
                rank_row = await cursor.fetchone()
            user_rank = rank_row[0] if rank_row else None

    return entries, user_rank, user_score


def format_leaderboard(
    entries: list[LeaderboardEntry],
    view: str,
    user_rank: int | None,
    user_score: float | int | None,
) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    view_titles = {
        "streak": "🔥 Лучший стрик",
        "solved": "✅ Всего решено",
        "accuracy": "🎯 Точность",
    }
    suffix = {"streak": "", "solved": "", "accuracy": "%"}

    title = view_titles.get(view, "🏆 Лидерборд")
    lines = [f"🏆 Лидерборд — {title}\n"]

    if not entries:
        lines.append("Пока нет данных.")
    else:
        for e in entries:
            medal = medals.get(e.rank, f"{e.rank}.")
            score_str = f"{e.score}{suffix[view]}"
            lines.append(f"{medal} {e.username} — {score_str}")

    if user_rank is not None and user_score is not None:
        score_str = f"{user_score}{suffix[view]}"
        lines.append(f"\n──────────────\n📍 Ты — #{user_rank} ({score_str})")

    return "\n".join(lines)
