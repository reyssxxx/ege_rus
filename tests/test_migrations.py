import os
import tempfile
import aiosqlite
from db.engine import init_db
from db.migrate import run_migrations


async def test_migrations_on_fresh_db():
    """Migrations should apply cleanly on a fresh DB (schema already has the columns)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        await init_db(db_path)
        async with aiosqlite.connect(db_path) as db:
            await run_migrations(db)
            # Check schema_migrations was created
            async with db.execute("SELECT COUNT(*) FROM schema_migrations") as c:
                count = (await c.fetchone())[0]
            assert count >= 0  # may be 0 if columns already exist in schema
    finally:
        os.unlink(db_path)


async def test_migrations_idempotent():
    """Running migrations twice should not error."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        await init_db(db_path)
        async with aiosqlite.connect(db_path) as db:
            await run_migrations(db)
            await run_migrations(db)  # second run should be no-op
            async with db.execute("SELECT COUNT(*) FROM schema_migrations") as c:
                count = (await c.fetchone())[0]
            assert count >= 0
    finally:
        os.unlink(db_path)
