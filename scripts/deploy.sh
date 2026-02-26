#!/bin/bash
# Скрипт для развертывания Traffk MVP на VPS

set -e  # Остановка при ошибке

echo "🚀 Развертывание Traffk MVP на VPS"
echo "=================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Пожалуйста, запустите скрипт с sudo${NC}"
    exit 1
fi

# Переменные (можно изменить)
APP_USER="traffk"
APP_DIR="/opt/traffk"
SERVICE_NAME="traffk-bot"

echo -e "${GREEN}📦 Шаг 1: Установка системных зависимостей${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib git

echo -e "${GREEN}👤 Шаг 2: Создание пользователя приложения${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    echo -e "${GREEN}✅ Пользователь $APP_USER создан${NC}"
else
    echo -e "${YELLOW}⚠️  Пользователь $APP_USER уже существует${NC}"
fi

echo -e "${GREEN}📁 Шаг 3: Создание директории приложения${NC}"
mkdir -p "$APP_DIR"
chown "$APP_USER:$APP_USER" "$APP_DIR"

echo -e "${GREEN}🗄️  Шаг 4: Настройка PostgreSQL${NC}"
echo "Введите пароль для пользователя БД traffk_user:"
read -s DB_PASSWORD

sudo -u postgres psql <<EOF
-- Создание базы данных и пользователя
CREATE DATABASE traffk_db;
CREATE USER traffk_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE traffk_db TO traffk_user;
\q
EOF

echo -e "${GREEN}✅ База данных создана${NC}"

echo -e "${GREEN}📥 Шаг 5: Копирование файлов приложения${NC}"
echo "Укажите путь к директории с проектом (или нажмите Enter для текущей):"
read -r SOURCE_DIR
SOURCE_DIR=${SOURCE_DIR:-$(pwd)}

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Директория $SOURCE_DIR не найдена${NC}"
    exit 1
fi

# Копируем файлы
sudo -u "$APP_USER" cp -r "$SOURCE_DIR"/* "$APP_DIR/" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Используем git clone...${NC}"
    echo "Введите URL репозитория (или нажмите Enter чтобы пропустить):"
    read -r REPO_URL
    if [ -n "$REPO_URL" ]; then
        sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    fi
}

echo -e "${GREEN}🐍 Шаг 6: Настройка Python окружения${NC}"
sudo -u "$APP_USER" bash <<EOF
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

echo -e "${GREEN}⚙️  Шаг 7: Настройка переменных окружения${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Создайте файл .env:"
    echo "BOT_TOKEN=your_bot_token"
    echo "DATABASE_URL=postgresql+asyncpg://traffk_user:$DB_PASSWORD@localhost:5432/traffk_db"
    echo "ADMIN_IDS=your_telegram_id"
    echo ""
    echo "Отредактируйте $APP_DIR/.env после завершения установки"
else
    echo -e "${GREEN}✅ Файл .env уже существует${NC}"
fi

echo -e "${GREEN}🗄️  Шаг 8: Применение миграций БД${NC}"
sudo -u "$APP_USER" bash <<EOF
cd "$APP_DIR"
source venv/bin/activate
alembic upgrade head
EOF

echo -e "${GREEN}🔧 Шаг 9: Создание systemd сервиса${NC}"
cat > "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=Traffk Telegram Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}✅ Сервис создан и включен${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте $APP_DIR/.env и укажите:"
echo "   - BOT_TOKEN (получите у @BotFather)"
echo "   - ADMIN_IDS (ваш Telegram ID)"
echo ""
echo "2. Запустите бота:"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "4. Просмотр логов:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo ""
