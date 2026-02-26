# 🚀 Быстрый старт Traffk MVP

## Шаг 1: Установка зависимостей

```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate для Windows

# Установите зависимости
pip install -r requirements.txt
```

## Шаг 2: Настройка базы данных

```bash
# Установите PostgreSQL (если еще не установлен)
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# macOS (через Homebrew):
brew install postgresql
brew services start postgresql

# Создайте базу данных
createdb traffk_db
# или через psql:
psql -U postgres
CREATE DATABASE traffk_db;
CREATE USER traffk_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE traffk_db TO traffk_user;
\q
```

## Шаг 3: Настройка переменных окружения

```bash
# Скопируйте пример файла
cp .env.example .env

# Отредактируйте .env и укажите:
# - BOT_TOKEN (получите у @BotFather в Telegram)
# - DATABASE_URL (например: postgresql+asyncpg://traffk_user:your_password@localhost:5432/traffk_db)
# - ADMIN_IDS (ваш Telegram ID, можно несколько через запятую)
```

### Как получить BOT_TOKEN:
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

### Как получить Telegram ID:
1. Откройте Telegram и найдите [@userinfobot](https://t.me/userinfobot)
2. Бот покажет ваш ID
3. Добавьте ID в `ADMIN_IDS` в `.env`

## Шаг 4: Применение миграций

```bash
# Примените миграции базы данных
alembic upgrade head
```

## Шаг 5: Запуск бота

```bash
# Убедитесь, что виртуальное окружение активировано
python bot.py
```

Бот должен запуститься и начать отвечать на команды в Telegram!

## 🐳 Альтернатива: Запуск через Docker

```bash
# Создайте .env файл (см. шаг 3)

# Запустите через docker-compose
docker-compose up -d

# Примените миграции
docker-compose exec bot alembic upgrade head

# Просмотр логов
docker-compose logs -f bot
```

## ✅ Проверка работы

1. Найдите вашего бота в Telegram (по имени, которое вы указали при создании)
2. Отправьте команду `/start`
3. Выберите роль
4. Попробуйте создать задание или просмотреть ленту

## 🔧 Полезные команды

```bash
# Просмотр логов
tail -f logs/bot.log

# Остановка бота (если запущен в терминале)
Ctrl+C

# Остановка Docker контейнеров
docker-compose down

# Перезапуск бота (Docker)
docker-compose restart bot
```

## ❗ Решение проблем

### Бот не отвечает
- Проверьте правильность BOT_TOKEN в `.env`
- Убедитесь, что бот запущен
- Проверьте логи: `tail -f logs/bot.log`

### Ошибки подключения к БД
- Проверьте, что PostgreSQL запущен: `sudo systemctl status postgresql`
- Проверьте правильность DATABASE_URL в `.env`
- Убедитесь, что пользователь БД имеет права доступа

### Ошибки миграций
```bash
# Откатить последнюю миграцию
alembic downgrade -1

# Применить все миграции
alembic upgrade head
```

## 📚 Дополнительная информация

Подробная документация доступна в [README.md](README.md)
