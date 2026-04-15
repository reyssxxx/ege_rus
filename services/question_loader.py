import json
import logging
import os
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

JSON_FILES = [
    "task_02_morphology.json",
    "task_04_orthoepy.json",
    "task_05_paronyms.json",
    "task_09_roots.json",
    "task_09_dictionary.json",
    "task_10_prefixes.json",
    "task_11_suffixes.json",
    "task_12_verb_endings.json",
    "task_14_spelling.json",
    "task_15_n_nn.json",
]


async def load_questions_if_needed(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Check if JSON files are newer than last load
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM questions")
        row = await cursor.fetchone()
        db_has_data = row["cnt"] > 0

        if db_has_data:
            # Compare modification times: if any JSON is newer than DB, reload
            db_mtime = os.path.getmtime(db_path)
            any_newer = any(
                (DATA_DIR / f).exists() and (DATA_DIR / f).stat().st_mtime > db_mtime
                for f in JSON_FILES
            )
            if not any_newer:
                return
            await db.execute("DELETE FROM questions")

        questions_to_insert = []

        for filename in JSON_FILES:
            filepath = DATA_DIR / filename
            if not filepath.exists():
                logger.warning("JSON file not found: %s", filepath)
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in %s: %s", filepath, e)
                continue

            task_number = data.get("task_number")
            if task_number is None:
                logger.warning("Missing task_number in %s", filepath)
                continue

            for subcat in data.get("subcategories", []):
                subcategory = subcat.get("name")
                for q in subcat.get("questions", []):
                    questions_to_insert.append((
                        task_number,
                        subcategory,
                        q["word_display"],
                        q["correct_answer"],
                        json.dumps(q["wrong_options"], ensure_ascii=False),
                        q["explanation"],
                    ))

        if questions_to_insert:
            await db.executemany(
                """
                INSERT INTO questions (task_number, subcategory, word_display, correct_answer, wrong_options, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                questions_to_insert,
            )
            logger.info("Loaded %d questions from JSON files", len(questions_to_insert))

        await db.commit()
