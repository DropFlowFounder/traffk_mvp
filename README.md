# 🚀 Traffk MVP - Telegram-бот с эскроу-гарантией

Telegram-бот для безопасных P2P-сделок в арбитраже трафика с ручным эскроу-сервисом.

## 📋 Описание

Traffk MVP - это платформа для безопасных сделок между рекламодателями и исполнителями трафика. Бот обеспечивает безопасность сделок через систему эскроу, где средства блокируются до подтверждения выполнения работы.

## ✨ Основные возможности

- ✅ Регистрация пользователей с выбором роли (Рекламодатель/Исполнитель)
- ✅ Создание и управление заданиями
- ✅ Лента заданий с фильтрацией
- ✅ Система proof (доказательства выполнения)
- ✅ Ручное управление эскроу администратором
- ✅ Система споров и арбитража
- ✅ Финансовые операции (депозит, вывод)
- ✅ Админ-панель для управления

## 🛠 Технологический стек

- **Python 3.11+**
- **aiogram 3.x** - асинхронный Telegram Bot API
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL 14+** - база данных
- **Alembic** - миграции БД
- **Docker** - контейнеризация (опционально)

## 📦 Установка и запуск

### Локальная установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository_url>
cd Traffk_mvp_beta_ai_cursor
```

2. **Создайте виртуальное окружение:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env и укажите:
# - BOT_TOKEN (получите у @BotFather)
# - DATABASE_URL (строка подключения к PostgreSQL)
# - ADMIN_IDS (ваш Telegram ID, можно несколько через запятую)
```

5. **Настройте базу данных:**
```bash
# Создайте базу данных PostgreSQL
createdb traffk_db

# Инициализируйте миграции Alembic
alembic init alembic  # если еще не инициализировано

# Примените миграции
alembic upgrade head
```

6. **Запустите бота:**
```bash
python bot.py
```

### Запуск через Docker

1. **Создайте файл .env** (см. шаг 4 выше)

2. **Запустите через docker-compose:**
```bash
docker-compose up -d
```

3. **Примените миграции:**
```bash
docker-compose exec bot alembic upgrade head
```

## 🔧 Конфигурация

### Переменные окружения (.env)

```env
# Telegram Bot Token (обязательно)
BOT_TOKEN=your_bot_token_here

# Database (обязательно)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/traffk_db

# Admin Telegram IDs (обязательно, через запятую)
ADMIN_IDS=123456789,987654321

# Sentry DSN (опционально, для отслеживания ошибок)
SENTRY_DSN=

# Environment
ENVIRONMENT=production
```

### Получение BOT_TOKEN

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### Получение Telegram ID

1. Откройте Telegram и найдите [@userinfobot](https://t.me/userinfobot)
2. Бот покажет ваш ID
3. Добавьте ID в `ADMIN_IDS` в `.env`

## 📚 Структура проекта

```
Traffk_mvp_beta_ai_cursor/
├── alembic/              # Миграции базы данных
│   ├── versions/         # Файлы миграций
│   ├── env.py           # Конфигурация Alembic
│   └── script.py.mako   # Шаблон миграций
├── handlers/             # Обработчики команд и callback
│   ├── __init__.py
│   ├── common.py        # Общие команды (start, help, profile)
│   ├── tasks.py         # Управление заданиями
│   ├── tasks_list.py    # Лента заданий
│   ├── proof.py         # Proof и подтверждение
│   ├── finance.py       # Финансовые операции
│   └── admin.py         # Админ-панель
├── logs/                # Логи приложения
├── bot.py               # Главный файл запуска
├── config.py            # Конфигурация
├── database.py          # Настройка БД
├── models.py            # Модели SQLAlchemy
├── keyboards.py         # Inline-клавиатуры
├── utils.py             # Вспомогательные функции
├── requirements.txt     # Зависимости Python
├── Dockerfile           # Docker образ
├── docker-compose.yml   # Docker Compose конфигурация
└── README.md           # Документация
```

## 🎯 Основные команды бота

### Для всех пользователей:
- `/start` - Регистрация и начало работы
- `/help` - Справка по использованию
- `/balance` - Просмотр баланса
- `/deposit` - Инструкция по пополнению
- `/withdraw` - Запрос на вывод средств

### Для рекламодателей:
- Создание заданий через меню
- Просмотр своих заданий
- Подтверждение/отклонение выполненных работ

### Для исполнителей:
- Просмотр ленты заданий
- Взятие заданий в работу
- Отправка proof выполнения

### Для администраторов:
- `/admin` - Админ-панель
- Управление депозитами и выплатами
- Разрешение споров
- Просмотр статистики

## 🔐 Безопасность

- Все платежи проходят через ручное подтверждение администратора
- Никакие платёжные данные не хранятся в боте
- Telegram ID используется как единственный идентификатор
- Whitelist для админ-команд

## 📊 База данных

### Основные таблицы:

- **users** - Пользователи бота
- **tasks** - Задания
- **transactions** - Транзакции (депозиты, выплаты, комиссии)
- **disputes** - Споры

Подробная схема БД описана в `models.py`.

## 🚀 Развёртывание на VPS

### Рекомендуемые требования:
- Ubuntu 22.04 LTS
- 1 GB RAM
- 10 GB SSD
- PostgreSQL 14+

### Шаги развёртывания:

1. **Установите зависимости:**
```bash
sudo apt update
sudo apt install python3-pip postgresql postgresql-contrib
```

2. **Создайте базу данных:**
```bash
sudo -u postgres psql
CREATE DATABASE traffk_db;
CREATE USER traffk_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE traffk_db TO traffk_user;
\q
```

3. **Настройте бота:**
```bash
git clone <repository_url>
cd Traffk_mvp_beta_ai_cursor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env
```

4. **Настройте systemd service:**
```bash
sudo nano /etc/systemd/system/traffk-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Traffk Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Traffk_mvp_beta_ai_cursor
Environment="PATH=/path/to/Traffk_mvp_beta_ai_cursor/venv/bin"
ExecStart=/path/to/Traffk_mvp_beta_ai_cursor/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **Запустите сервис:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable traffk-bot
sudo systemctl start traffk-bot
sudo systemctl status traffk-bot
```

## 🐛 Решение проблем

### Бот не отвечает:
- Проверьте правильность BOT_TOKEN в .env
- Убедитесь, что бот запущен: `ps aux | grep bot.py`
- Проверьте логи: `tail -f logs/bot.log`

### Ошибки подключения к БД:
- Проверьте DATABASE_URL в .env
- Убедитесь, что PostgreSQL запущен: `sudo systemctl status postgresql`
- Проверьте права доступа пользователя БД

### Проблемы с миграциями:
```bash
# Откатить последнюю миграцию
alembic downgrade -1

# Применить все миграции
alembic upgrade head
```

## 📝 Лицензия

Этот проект создан для MVP и может быть использован в коммерческих целях.

## 🤝 Поддержка

По вопросам и предложениям обращайтесь к администратору проекта.

---

**Версия:** 1.0.0 MVP  
**Дата:** 2024
