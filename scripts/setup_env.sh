#!/bin/bash
# Интерактивный скрипт для настройки .env файла

set -e

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

echo "🔧 Настройка переменных окружения для Traffk MVP"
echo "=================================================="

# Проверяем наличие .env.example
if [ ! -f "$ENV_EXAMPLE" ]; then
    echo "❌ Файл $ENV_EXAMPLE не найден!"
    exit 1
fi

# Создаем .env из примера, если его нет
if [ ! -f "$ENV_FILE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "✅ Создан файл $ENV_FILE из примера"
fi

echo ""
echo "Введите значения для переменных окружения:"
echo ""

# BOT_TOKEN
echo "1️⃣  BOT_TOKEN (токен бота от @BotFather)"
echo "   Получите у @BotFather в Telegram командой /newbot"
read -p "   BOT_TOKEN: " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
    sed -i.bak "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" "$ENV_FILE"
fi

echo ""

# DATABASE_URL
echo "2️⃣  DATABASE_URL (строка подключения к PostgreSQL)"
echo "   Формат: postgresql+asyncpg://user:password@host:port/database"
read -p "   DATABASE_URL [postgresql+asyncpg://traffk_user:password@localhost:5432/traffk_db]: " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    DATABASE_URL="postgresql+asyncpg://traffk_user:password@localhost:5432/traffk_db"
fi
sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$ENV_FILE"

echo ""

# ADMIN_IDS
echo "3️⃣  ADMIN_IDS (ваш Telegram ID, можно несколько через запятую)"
echo "   Получите у @userinfobot в Telegram"
read -p "   ADMIN_IDS: " ADMIN_IDS
if [ -n "$ADMIN_IDS" ]; then
    sed -i.bak "s|ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_IDS|" "$ENV_FILE"
fi

echo ""

# SENTRY_DSN (опционально)
echo "4️⃣  SENTRY_DSN (опционально, для отслеживания ошибок)"
read -p "   SENTRY_DSN [оставить пустым]: " SENTRY_DSN
if [ -n "$SENTRY_DSN" ]; then
    sed -i.bak "s|SENTRY_DSN=.*|SENTRY_DSN=$SENTRY_DSN|" "$ENV_FILE"
else
    sed -i.bak "s|SENTRY_DSN=.*|SENTRY_DSN=|" "$ENV_FILE"
fi

echo ""

# ENVIRONMENT
echo "5️⃣  ENVIRONMENT (development или production)"
read -p "   ENVIRONMENT [development]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-development}
sed -i.bak "s|ENVIRONMENT=.*|ENVIRONMENT=$ENVIRONMENT|" "$ENV_FILE"

# Удаляем backup файлы
rm -f "$ENV_FILE.bak"

echo ""
echo "✅ Файл $ENV_FILE настроен!"
echo ""
echo "Проверьте содержимое файла:"
echo "---"
cat "$ENV_FILE"
echo "---"
echo ""
echo "Для проверки конфигурации запустите:"
echo "  python scripts/check_config.py"
