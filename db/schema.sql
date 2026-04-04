CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_number INTEGER NOT NULL,
    subcategory TEXT,
    word_display TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    wrong_options TEXT NOT NULL,  -- JSON array
    explanation TEXT NOT NULL,
    difficulty INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_questions_task ON questions(task_number);
CREATE INDEX IF NOT EXISTS idx_questions_task_sub ON questions(task_number, subcategory);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT NOT NULL,
    last_active TEXT NOT NULL,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_streak_date TEXT,
    session_streak INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    is_correct INTEGER NOT NULL,
    answered_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_answers_user ON user_answers(user_id, answered_at);
CREATE INDEX IF NOT EXISTS idx_user_answers_user_q ON user_answers(user_id, question_id);

CREATE TABLE IF NOT EXISTS user_question_stats (
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    times_shown INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_shown TEXT,
    PRIMARY KEY (user_id, question_id)
);

CREATE VIEW IF NOT EXISTS user_category_stats AS
SELECT
    ua.user_id,
    q.task_number,
    q.subcategory,
    COUNT(*) AS total_answers,
    SUM(ua.is_correct) AS correct_answers,
    ROUND(100.0 * SUM(ua.is_correct) / COUNT(*), 1) AS accuracy_pct
FROM user_answers ua
JOIN questions q ON ua.question_id = q.id
GROUP BY ua.user_id, q.task_number, q.subcategory;
