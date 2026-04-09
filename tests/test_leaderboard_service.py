from services.leaderboard_service import format_leaderboard, LeaderboardEntry, get_leaderboard
from db.repositories.users import ensure_user
from db.repositories.answers import record_answer
import json


def test_format_leaderboard_empty():
    text = format_leaderboard([], "streak", None, None)
    assert "Пока нет данных" in text


def test_format_leaderboard_with_entries():
    entries = [
        LeaderboardEntry(rank=1, user_id=1, username="ivan", score=47),
        LeaderboardEntry(rank=2, user_id=2, username="masha", score=31),
    ]
    text = format_leaderboard(entries, "streak", None, None)
    assert "🥇" in text
    assert "ivan" in text
    assert "47" in text
    assert "🥈" in text


def test_format_leaderboard_with_self_position():
    entries = [LeaderboardEntry(rank=1, user_id=1, username="ivan", score=47)]
    text = format_leaderboard(entries, "streak", 14, 12)
    assert "#14" in text
    assert "12" in text


async def test_get_leaderboard_streak(db):
    """Test that leaderboard returns users sorted by streak."""
    # Insert test users
    await ensure_user(db, 100, "alice")
    await ensure_user(db, 200, "bob")
    await db.execute("UPDATE users SET longest_streak = 10 WHERE user_id = 100")
    await db.execute("UPDATE users SET longest_streak = 20 WHERE user_id = 200")
    await db.commit()

    entries, user_rank, user_score = await get_leaderboard(db, "streak", 100)
    assert len(entries) == 2
    assert entries[0].username == "bob"
    assert entries[0].score == 20


async def test_get_leaderboard_accuracy_min_threshold(db):
    """Users with < 20 answers should NOT appear in accuracy leaderboard."""
    await ensure_user(db, 100, "alice")
    # Insert a question first
    await db.execute(
        """INSERT INTO questions (id, task_number, subcategory, word_display, correct_answer, wrong_options, explanation)
           VALUES (1, 4, 'main', 'test', 'correct', '["wrong1","wrong2"]', 'expl')"""
    )
    # Give alice only 5 answers
    for _ in range(5):
        await record_answer(db, 100, 1, True)
    await db.commit()

    entries, _, _ = await get_leaderboard(db, "accuracy", 100)
    assert len(entries) == 0  # alice has < 20 answers
