# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt

# Run bot
.venv/Scripts/python bot.py

# Reload question data (delete DB so loader re-imports from JSON on next start)
rm data/ege_bot.db

# Convert raw Quizlet data into question JSON
.venv/Scripts/python scripts/convert_task09.py

# Syntax check all files
.venv/Scripts/python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True) if '.venv' not in f]"
```

## Architecture

**Entry point:** `bot.py` — creates Bot/Dispatcher, registers middleware, calls `init_db` + `load_questions_if_needed`, starts polling.

**Request lifecycle:** Every message/callback goes through `DbSessionMiddleware` (injects `db: aiosqlite.Connection`) → FSM state filter → handler → auto-commit on exit.

**Quiz flow (FSM):**
`choosing_category` → `choosing_subcategory` → `answering` → `reviewing` → (loop)

After the user answers, `handlers/quiz.py` shows feedback, sleeps `FEEDBACK_DELAY` seconds, then auto-advances to the next question by calling `send_question()` again. There is no "Next" button — the loop is automatic. The only controls during a session are **Стоп** and **Сменить тему**.

**CallbackData constraint:** Telegram limits `callback_data` to 64 bytes. Answer options are encoded as `answer_index: int` (position in the shuffled list), with the shuffled list stored in FSM state under `options_order`.

**Question data pipeline:**
1. Authored in `data/*.json` (human-editable)
2. On startup, `services/question_loader.py` checks if any JSON is newer than the DB file — if so, wipes and re-imports all questions
3. Runtime queries go through `db/repositories/questions.py` which uses `user_question_stats` for weighted selection (wrong answers get higher weight)

**Session state keys** (stored in FSM `data`):
- `task_number`, `subcategory` — current category filter
- `streak` — consecutive correct answers (resets to 0 on wrong)
- `session_total` — total answers this session
- `current_question_id`, `options_order` — active question

**Adding a new task/category:** Create a new `data/task_NN_name.json` following the existing schema, add the filename to `JSON_FILES` in `services/question_loader.py`, add the task number to `TASK_NAMES`/`TASK_DESCRIPTIONS` in `utils/constants.py`, delete the DB to trigger reload.

**Stress marks in Task 4:** Use uppercase for the stressed letter (`сирОты`, not `сиро́ты`). The display word shows no stress; options are the full word with one letter capitalised.
