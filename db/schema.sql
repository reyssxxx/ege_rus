-- Вопросы для заданий ЕГЭ
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_number INTEGER NOT NULL,        -- Номер задания (4, 5, 9-12, 14, 15)
    subcategory TEXT,                    -- Подкатегория (например, "чередующиеся корни")
    word_display TEXT NOT NULL,          -- Слово/предложение для показа пользователю
    correct_answer TEXT NOT NULL,        -- Правильный ответ
    wrong_options TEXT NOT NULL,         -- JSON массив неправильных вариантов
    explanation TEXT NOT NULL,           -- Пояснение к ответу
    difficulty INTEGER DEFAULT 1         -- Сложность (1-3, пока не используется)
);

CREATE INDEX IF NOT EXISTS idx_questions_task ON questions(task_number);
CREATE INDEX IF NOT EXISTS idx_questions_task_sub ON questions(task_number, subcategory);

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,         -- Telegram user_id
    username TEXT,                       -- Имя пользователя Telegram
    first_seen TEXT NOT NULL,            -- Дата первой регистрации (ISO)
    last_active TEXT NOT NULL,           -- Дата последней активности (ISO)
    longest_streak INTEGER DEFAULT 0,    -- Лучший стрик за всё время (правильных ответов подряд)
    reminder_enabled INTEGER NOT NULL DEFAULT 1,
    last_active_date TEXT
);

-- Ответы пользователей (история)
CREATE TABLE IF NOT EXISTS user_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    is_correct INTEGER NOT NULL,         -- 1 = правильно, 0 = неправильно
    answered_at TEXT NOT NULL            -- Дата ответа (ISO)
);

CREATE INDEX IF NOT EXISTS idx_user_answers_user ON user_answers(user_id, answered_at);
CREATE INDEX IF NOT EXISTS idx_user_answers_user_q ON user_answers(user_id, question_id);

-- Статистика по вопросам (для взвешенного подбора)
CREATE TABLE IF NOT EXISTS user_question_stats (
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    times_shown INTEGER DEFAULT 0,       -- Сколько раз показан
    times_correct INTEGER DEFAULT 0,     -- Сколько раз отвечен правильно
    last_shown TEXT,                     -- Дата последнего показа (ISO)
    PRIMARY KEY (user_id, question_id)
);

-- Представление: статистика по заданиям
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
