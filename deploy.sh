#!/bin/bash
# Автоматический скрипт деплоя EGE Bot
# Запускать: bash <(curl -sL https://raw.githubusercontent.com/reyssxxx/ege_rus/main/deploy.sh)

set -e

BOT_DIR="/opt/ege_bot"
REPO_URL="https://github.com/reyssxxx/ege_rus.git"

echo "=== EGE Bot Deployment ==="
echo "Установка зависимостей..."

# Обновление пакетов и установка Python
apt update -y
apt install -y python3 python3-pip python3-venv git

# Клонирование репозитория
echo "Клонирование репозитория..."
mkdir -p $BOT_DIR
cd $BOT_DIR
git clone $REPO_URL . 2>/dev/null || {
    echo "Обновление существующего репозитория..."
    git pull origin main 2>/dev/null || true
}

# Создание .env файла (если не существует)
if [ ! -f .env ]; then
    echo "Создание .env файла..."
    cat > .env << EOF
BOT_TOKEN=your_telegram_bot_token_here
DB_PATH=data/ege_bot.db
EOF
    echo "⚠️  ВАЖНО: Укажите BOT_TOKEN в файле $BOT_DIR/.env"
    echo "   Затем запустите: systemctl restart ege-bot"
fi

# Создание виртуального окружения
echo "Настройка Python окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
if [ -f "requirements.txt" ]; then
    echo "Установка Python зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Создание systemd service
echo "Настройка systemd service..."
cat > /etc/systemd/system/ege-bot.service << EOF
[Unit]
Description=EGE Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
EnvironmentFile=$BOT_DIR/.env
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Активация и запуск service
systemctl daemon-reload
systemctl enable ege-bot
systemctl restart ege-bot

echo ""
echo "=== Деплой завершён! ==="
echo "Статус бота: systemctl status ege-bot"
echo "Логи: journalctl -u ege-bot -f"
echo "Остановить: systemctl stop ege-bot"
echo "Перезапустить: systemctl restart ege-bot"
