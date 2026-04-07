# EGE Bot — Телеграм-бот для подготовки к ЕГЭ по русскому языку

## Обзор проекта

**ege_bot** — это Telegram-бот, помогающий школьникам готовиться к ЕГЭ по русскому языку. Бот проводит интерактивные викторины по различным орфографическим и лингвистическим заданиям (задания 4, 5, 9–12, 14, 15), адаптируя сложность на основе результатов пользователя.

### Технологии

- **Python 3.10+** (используются union-типы `int | None`)
- **aiogram 3.x** — асинхронный фреймворк для Telegram Bot API
- **aiosqlite** — асинхронная работа с SQLite
- **pydantic-settings** — управление конфигурацией через `.env`
- **FSM** (Finite State Machine) — управление состоянием викторины

## Архитектура

### Entry point

- **`bot.py`** — создаёт бота и диспетчер, регистрирует middleware, инициализирует БД, загружает вопросы, запускает polling.

### Структура директорий

```
bot.py                  # Точка входа
config.py               # Настройки (pydantic-settings)
handlers/               # Обработчики сообщений и callback-запросов
  start.py              # Команда /start
  category.py           # Выбор задания/подкатегории
  quiz.py               # Основной движок викторины
  stats.py              # Статистика пользователя
keyboards/              # Inline-клавиатуры и CallbackData-фильтры
  callbacks.py          # QuizAnswer, QuizControl, TaskStart (CallbackData)
  category.py           # Клавиатура выбора заданий
  quiz.py               # Клавиатуры ответов и управления
  menu.py               # Главное меню
  stats.py              # Клавиатуры статистики
middlewares/
  db_session.py         # Инжектирует aiosqlite.Connection в каждый handler
services/
  question_loader.py    # Загрузка вопросов из JSON в БД
  quiz_engine.py        # Логика выбора вопроса, формирования вариантов, проверки
states/
  quiz.py               # QuizState FSM (choosing_category, answering, reviewing)
db/
  engine.py             # Инициализация БД
  schema.sql            # SQL-схема таблиц и представлений
  models.py             # Pydantic-модели (Question, User, etc.)
  repositories/         # DAO-слой для работы с БД
data/
  task_XX_*.json        # Файлы с вопросами по заданиям
utils/
  constants.py          # TASK_NAMES, TASK_DESCRIPTIONS
  formatting.py         # Форматирование текстов вопросов и обратной связи
  safe_edit.py          # Безопасное редактижение сообщений
scripts/
  convert_task09.py     # Скрипт конвертации сырых Quizlet-данных в JSON
```

### Поток викторины (FSM)

```
choosing_category → choosing_subcategory → answering → reviewing → (цикл)
```

1. Пользователь выбирает задание (например, «Задание 9 — Корни»).
2. Бот выбирает вопрос через **взвешенный алгоритм** (ошибочные вопросы показываются чаще).
3. Пользователь отвечает — бот показывает обратную связь.
4. Для коротких заданий — **авто-переход** через `FEEDBACK_DELAY` (0.8 сек).
5. Для заданий с длинными пояснениями — кнопка **«Продолжить»**.
6. При ошибке — сессия останавливается, предлагается **перезапуск**.

### Система данных

- **Вопросы** хранятся в `data/task_XX_*.json` и загружаются в SQLite при старте.
- При запуске `question_loader.py` сравнивает время модификации JSON и БД — если JSON новее, данные перезагружаются.
- Статистика ответов хранится в `user_question_stats` для взвешенного отбора.
- Telegram `callback_data` ограничен 64 байтами — варианты кодируются как `answer_index: int`, порядок хранится в FSM-состоянии (`options_order`).

## Установка и запуск

### Первичная настройка

```bash
# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл (скопировать из .env.example и заполнить)
copy .env.example .env
```

### Запуск бота

```bash
python bot.py
```

### Перезагрузка вопросов

Удалить БД, чтобы loader повторно импортировал вопросы из JSON:

```bash
del data\ege_bot.db   # Windows
```

### Конвертация сырых данных Quizlet

```bash
python scripts\convert_task09.py
```

### Проверка синтаксиса всех файлов

```bash
python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True) if '.venv' not in f]"
```

## Добавление нового задания

1. Создать файл `data/task_NN_name.json` по существующей схеме.
2. Добавить имя файла в `JSON_FILES` в `services/question_loader.py`.
3. Добавить номер задания в `TASK_NAMES` и `TASK_DESCRIPTIONS` в `utils/constants.py`.
4. Удалить БД для триггера перезагрузки: `del data\ege_bot.db`.

## Схема вопросов (JSON)

```json
{
  "task_number": 9,
  "subcategories": [
    {
      "name": "Чередующиеся корни",
      "questions": [
        {
          "word_display": "заг_рать",
          "correct_answer": "а",
          "wrong_options": ["о"],
          "explanation": "В корне -гар-/-гор- пишется А, если после корня нет суффикса -а-."
        }
      ]
    }
  ]
}
```

## База данных

### Таблицы

| Таблица | Описание |
|---------|----------|
| `questions` | Вопросы с вариантами ответов |
| `users` | Пользователи с текущей/максимальной серией |
| `user_answers` | История ответов пользователя |
| `user_question_stats` | Статистика по каждому вопросу (для взвешенного отбора) |

### Представления

| Представление | Описание |
|---------------|----------|
| `user_category_stats` | Точность ответов по заданиям/подкатегориям |

## Соглашения

- **Ударения в задании 4**: Используется **верхний регистр** для ударной буквы (`сирОты`), а не комбинированные символы ударения.
- **Авто-переход**: Если пояснение короче 50 символов — авто-переход; иначе — кнопка «Продолжить».
- **Серия (streak)**: При ошибке серия сбрасывается, а если предыдущая серия была рекордной — обновляется `longest_streak` в БД.
- **Безопасность сообщений**: Используется `safe_edit_text` для предотвращения ошибок при редактировании неактуальных сообщений.
