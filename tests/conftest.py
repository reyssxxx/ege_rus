import os
import tempfile
import pytest
import aiosqlite

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.engine import init_db
from db.migrate import run_migrations


@pytest.fixture
async def db():
    """Create a temp SQLite DB with schema + migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        await init_db(db_path)
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row
        await run_migrations(conn)
        yield conn
        await conn.close()
    finally:
        os.unlink(db_path)


@pytest.fixture
def sample_question():
    """A sample Question for tests."""
    from db.models import Question
    return Question(
        id=1,
        task_number=4,
        subcategory="main",
        word_display="аэропорты",
        correct_answer="аэропОрты",
        wrong_options=["Аэропорты", "аЭропорты"],
        explanation="Правильное ударение: аэропОрты.",
        difficulty=1,
    )
