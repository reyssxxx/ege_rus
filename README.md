# ЕГЭ Бот — Русский язык

Telegram-бот для подготовки к ЕГЭ по русскому языку. Тренировка заданий с выбором ответа.

## Возможности

- 📝 **Задания 4, 5, 9-12, 14, 15** — орфоэпия, паронимы, корни, приставки, суффиксы, окончания, spelling, Н/НН
- 🔀 **Режим "Все подряд"** — случайные вопросы из всех заданий
- 📊 **Статистика** — общая точность, прогресс по заданиям, проблемные слова
- 🔥 **Стрик** — серия правильных ответов с сохранением рекорда
- ⚡ **Умный подбор** — ошибки показываются чаще
- 💡 **Пояснения** — после каждого ответа

## Установка

### Требования
- Python 3.12+
- SQLite (встроен в Python)

### Шаги

1. Клонируйте репозиторий:
```bash
git clone https://github.com/reyssxxx/ege_rus.git
cd ege_rus
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте `.env` файл:
```bash
cp .env.example .env
```

5. Укажите токен бота в `.env`:
```
BOT_TOKEN=your_telegram_bot_token_here
DB_PATH=data/ege_bot.db
```

6. Запустите бота:
```bash
python bot.py
```

## Деплой на сервер

```bash
bash <(curl -sL https://raw.githubusercontent.com/reyssxxx/ege_rus/main/deploy.sh)
```

## Обновление

```bash
cd /opt/ege_bot && git pull && systemctl restart ege-bot
```

## Архитектура

```
├── bot.py              # Точка входа
├── config.py           # Настройки (pydantic-settings)
├── handlers/           # Обработчики сообщений
│   ├── start.py        # /start, главное меню
│   ├── category.py     # Выбор задания
│   ├── quiz.py         # Логика квиза
│   └── stats.py        # Статистика
├── keyboards/          # Inline-клавиатуры
├── middlewares/        # DbSessionMiddleware
├── services/           # Бизнес-логика (quiz_engine, stats_service, question_loader)
├── states/             # FSM состояния
├── db/                 # БД (schema, engine, manager, repositories)
├── data/               # JSON файлы с вопросами
└── utils/              # Утилиты (форматирование, константы)
```

## Технологии

- [aiogram 3.x](https://docs.aiogram.dev/) — Telegram Bot API
- [aiosqlite](https://aiosqlite.omnilib.dev/) — асинхронный SQLite
- [pydantic-settings](https://docs.pydantic.dev/) — настройки из .env
- WAL режим SQLite для конкурентных записей

## Лицензия

MIT
