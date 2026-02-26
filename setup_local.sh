#!/bin/bash
# Локальная настройка переменных окружения

echo "🔧 Настройка переменных окружения для Traffk MVP"
echo "=================================================="

# Проверяем наличие .env.example
if [ ! -f ".env.example" ]; then
    echo "❌ Файл .env.example не найден!"
    exit 1
fi

# Создаем .env из примера, если его нет
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Создан файл .env из примера"
else
    echo "⚠️  Файл .env уже существует. Будет обновлен."
fi

echo ""
echo "Введите значения для переменных окружения:"
echo ""

# BOT_TOKEN
echo "1️⃣  BOT_TOKEN (токен бота от @BotFather)"
echo "   Получите у @BotFather в Telegram командой /newbot"
read -p "   BOT_TOKEN: " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" .env
    else
        # Linux
        sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" .env
    fi
fi

echo ""

# DATABASE_URL
echo "2️⃣  DATABASE_URL (строка подключения к PostgreSQL)"
echo "   Формат: postgresql+asyncpg://user:password@host:port/database"
read -p "   DATABASE_URL [postgresql+asyncpg://traffk_user:password@localhost:5432/traffk_db]: " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    DATABASE_URL="postgresql+asyncpg://traffk_user:password@localhost:5432/traffk_db"
fi
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
else
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
fi

echo ""

# ADMIN_IDS
echo "3️⃣  ADMIN_IDS (ваш Telegram ID, можно несколько через запятую)"
echo "   Получите у @userinfobot в Telegram"
read -p "   ADMIN_IDS: " ADMIN_IDS
if [ -n "$ADMIN_IDS" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_IDS|" .env
    else
        sed -i "s|ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_IDS|" .env
    fi
fi

echo ""

# SENTRY_DSN (опционально)
echo "4️⃣  SENTRY_DSN (опционально, для отслеживания ошибок)"
read -p "   SENTRY_DSN [оставить пустым]: " SENTRY_DSN
if [ -n "$SENTRY_DSN" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SENTRY_DSN=.*|SENTRY_DSN=$SENTRY_DSN|" .env
    else
        sed -i "s|SENTRY_DSN=.*|SENTRY_DSN=$SENTRY_DSN|" .env
    fi
else
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SENTRY_DSN=.*|SENTRY_DSN=|" .env
    else
        sed -i "s|SENTRY_DSN=.*|SENTRY_DSN=|" .env
    fi
fi

echo ""

# ENVIRONMENT
echo "5️⃣  ENVIRONMENT (development или production)"
read -p "   ENVIRONMENT [development]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-development}
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|ENVIRONMENT=.*|ENVIRONMENT=$ENVIRONMENT|" .env
else
    sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=$ENVIRONMENT|" .env
fi

echo ""
echo "✅ Файл .env настроен!"
echo ""
echo "Проверьте содержимое файла:"
echo "---"
cat .env
echo "---"
echo ""
echo "Для проверки конфигурации запустите:"
echo "  python3 scripts/check_config.py"
