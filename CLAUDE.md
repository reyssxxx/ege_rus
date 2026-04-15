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

# Syntax check all project files
.venv/Scripts/python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True) if '.venv' not in f]"
```

## Architecture

**Entry point:** `bot.py` — runs migrations (`db/migrate.py`), calls `init_db`, creates a single `DatabaseManager` connection (WAL mode), registers middleware, starts polling.

**Request lifecycle:** Every message/callback goes through `DbSessionMiddleware` (injects `db: aiosqlite.Connection` from the shared `DatabaseManager`) → FSM state filter → handler.

**Quiz flow (FSM states in `states/quiz.py`):**
`choosing_category` → `answering` → `reviewing` → (loop back to `answering`)

- User selects tasks (multi-select with toggle), hits «Начать» → `send_question()` is called
- After answering: wrong answer or long explanation (`> LONG_EXPLANATION_THRESHOLD` chars) → show `continue_keyboard()` and wait; short correct answer → auto-advance after `FEEDBACK_DELAY` seconds
- Wrong answers no longer stop the session — streak resets to 0 but the quiz continues
- Controls during session: **Стоп** (shows session summary), **« Назад** (back to menu)

**FSM state keys** (stored in `state.data`):
- `task_number` — single task filter (None = all); `task_numbers` — list for multi-select mode
- `subcategory` — subcategory filter within a task
- `selected_tasks` — list of toggled task numbers during category selection
- `streak`, `best_streak` — current and personal best consecutive correct answers
- `session_total`, `session_correct`, `session_wrong` — per-session counters for summary
- `current_question_id`, `options_order` — active question

**CallbackData constraint:** Telegram limits `callback_data` to 64 bytes. Answer options are encoded as `answer_index: int` (position in the shuffled list); the shuffled list is stored in FSM state under `options_order`.

**Question data pipeline:**
1. Authored in `data/task_NN_name.json`
2. `services/question_loader.py` re-imports all JSON into SQLite on startup if any file is newer than the DB
3. `db/repositories/questions.py` uses weighted selection via `user_question_stats` (wrong answers surface more often); supports filtering by single `task_number`, `subcategory`, or a list `task_numbers`

**Database schema evolution:** Add a new file `db/migrations/NNN_description.sql` (zero-padded 3-digit prefix). Migrations run automatically on startup via `db/migrate.py` and are tracked in `schema_migrations`.

**Button styling:** Use `style="success"` on `InlineKeyboardButton` (Bot API 9.0) for active/selected state instead of emoji prefixes. Valid values: `"success"` (green), `"danger"` (red), `"primary"` (blue).

**Adding a new task/category:**
1. Create `data/task_NN_name.json` following the existing schema (`task_number`, `subcategories[].name`, `questions[].word_display/correct_answer/wrong_options/explanation`)
2. Add filename to `JSON_FILES` in `services/question_loader.py`
3. Add task number to `TASK_NAMES` / `TASK_DESCRIPTIONS` in `utils/constants.py`
4. Delete the DB to trigger reload

**Task-specific data conventions:**
- Task 4 (ударения): uppercase the stressed letter in options (`сирОты`). Display word has no mark; options are full words with one letter capitalised.
- Task 5 (паронимы): `word_display` is a full sentence with `_____`; `correct_answer` is the fitting word.
- Task 9 (словарные): `word_display` has `_` at the missing vowel position.
