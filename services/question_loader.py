import json
import os

import aiosqlite


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

JSON_FILES = [
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
                os.path.exists(os.path.join(DATA_DIR, f)) and os.path.getmtime(os.path.join(DATA_DIR, f)) > db_mtime
                for f in JSON_FILES
            )
            if not any_newer:
                return
            await db.execute("DELETE FROM questions")

        for filename in JSON_FILES:
            filepath = os.path.join(DATA_DIR, filename)
            if not os.path.exists(filepath):
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            task_number = data["task_number"]

            for subcat in data.get("subcategories", []):
                subcategory = subcat.get("name")
                for q in subcat.get("questions", []):
                    await db.execute(
                        """
                        INSERT INTO questions (task_number, subcategory, word_display, correct_answer, wrong_options, explanation)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            task_number,
                            subcategory,
                            q["word_display"],
                            q["correct_answer"],
                            json.dumps(q["wrong_options"], ensure_ascii=False),
                            q["explanation"],
                        ),
                    )

        await db.commit()
