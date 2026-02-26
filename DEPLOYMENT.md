# 🚀 Развертывание Traffk MVP на VPS

Подробное руководство по развертыванию бота на VPS сервере.

## 📋 Требования

- VPS с Ubuntu 22.04 LTS (или другой Linux дистрибутив)
- Минимум 1 GB RAM
- 10 GB свободного места
- Root доступ или sudo права
- Доменное имя (опционально, для webhook)

## 🔧 Вариант 1: Автоматическое развертывание

### Шаг 1: Подготовка проекта

```bash
# На вашем локальном компьютере
cd Traffk_mvp_beta_ai_cursor

# Создайте архив проекта (исключая ненужные файлы)
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.env' \
    -czf traffk.tar.gz .
```

### Шаг 2: Загрузка на VPS

```bash
# Загрузите архив на VPS
scp traffk.tar.gz user@your-vps-ip:/tmp/

# Подключитесь к VPS
ssh user@your-vps-ip
```

### Шаг 3: Запуск скрипта развертывания

```bash
# На VPS
cd /tmp
tar -xzf traffk.tar.gz
cd Traffk_mvp_beta_ai_cursor

# Сделайте скрипт исполняемым
chmod +x scripts/deploy.sh

# Запустите развертывание (требует sudo)
sudo ./scripts/deploy.sh
```

Скрипт автоматически:
- Установит зависимости
- Создаст пользователя приложения
- Настроит PostgreSQL
- Установит Python зависимости
- Создаст systemd сервис

### Шаг 4: Настройка переменных окружения

```bash
# Отредактируйте .env файл
sudo nano /opt/traffk/.env
```

Укажите:
- `BOT_TOKEN` - токен от @BotFather
- `DATABASE_URL` - строка подключения к БД
- `ADMIN_IDS` - ваш Telegram ID

### Шаг 5: Запуск бота

```bash
# Запустите сервис
sudo systemctl start traffk-bot

# Проверьте статус
sudo systemctl status traffk-bot

# Включите автозапуск (уже включен скриптом)
sudo systemctl enable traffk-bot
```

## 🔧 Вариант 2: Ручное развертывание

### Шаг 1: Установка системных зависимостей

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git
```

### Шаг 2: Создание пользователя приложения

```bash
sudo useradd -m -s /bin/bash traffk
sudo su - traffk
```

### Шаг 3: Настройка PostgreSQL

```bash
# Вернитесь в root
exit

# Создайте базу данных
sudo -u postgres psql
```

В psql выполните:
```sql
CREATE DATABASE traffk_db;
CREATE USER traffk_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE traffk_db TO traffk_user;
\q
```

### Шаг 4: Клонирование проекта

```bash
sudo su - traffk
cd ~
git clone <your-repo-url> traffk
# или скопируйте файлы проекта
cd traffk
```

### Шаг 5: Настройка Python окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 6: Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Или используйте интерактивный скрипт:
```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

### Шаг 7: Применение миграций

```bash
source venv/bin/activate
alembic upgrade head
```

### Шаг 8: Создание systemd сервиса

```bash
# Выйдите из пользователя traffk
exit

# Создайте файл сервиса
sudo nano /etc/systemd/system/traffk-bot.service
```

Вставьте следующее содержимое (замените пути при необходимости):

```ini
[Unit]
Description=Traffk Telegram Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=traffk
WorkingDirectory=/home/traffk/traffk
Environment="PATH=/home/traffk/traffk/venv/bin"
ExecStart=/home/traffk/traffk/venv/bin/python /home/traffk/traffk/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Шаг 9: Запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable traffk-bot
sudo systemctl start traffk-bot
sudo systemctl status traffk-bot
```

## 📊 Управление сервисом

### Просмотр статуса
```bash
sudo systemctl status traffk-bot
```

### Просмотр логов
```bash
# Последние логи
sudo journalctl -u traffk-bot -n 50

# Логи в реальном времени
sudo journalctl -u traffk-bot -f

# Логи за сегодня
sudo journalctl -u traffk-bot --since today
```

### Перезапуск
```bash
sudo systemctl restart traffk-bot
```

### Остановка
```bash
sudo systemctl stop traffk-bot
```

## 🔒 Безопасность

### Firewall (UFW)

```bash
# Разрешите SSH (важно сделать первым!)
sudo ufw allow 22/tcp

# Разрешите PostgreSQL только локально (по умолчанию)
# PostgreSQL не должен быть доступен извне

# Включите firewall
sudo ufw enable
```

### Резервное копирование БД

Создайте скрипт для резервного копирования:

```bash
sudo nano /opt/backup_traffk.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/traffk"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

sudo -u postgres pg_dump traffk_db > "$BACKUP_DIR/traffk_$DATE.sql"

# Удаляем старые бэкапы (старше 7 дней)
find "$BACKUP_DIR" -name "traffk_*.sql" -mtime +7 -delete
```

Сделайте исполняемым и добавьте в cron:
```bash
sudo chmod +x /opt/backup_traffk.sh
sudo crontab -e
# Добавьте строку:
0 2 * * * /opt/backup_traffk.sh
```

## 🔍 Проверка работы

### Проверка конфигурации

```bash
cd /opt/traffk  # или /home/traffk/traffk
source venv/bin/activate
python scripts/check_config.py
```

### Тестирование подключения к БД

```bash
sudo -u postgres psql -d traffk_db -c "SELECT COUNT(*) FROM users;"
```

### Проверка работы бота

1. Найдите бота в Telegram
2. Отправьте `/start`
3. Проверьте логи: `sudo journalctl -u traffk-bot -f`

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверьте логи
sudo journalctl -u traffk-bot -n 100

# Проверьте конфигурацию
python scripts/check_config.py

# Проверьте права доступа
sudo chown -R traffk:traffk /opt/traffk
```

### Ошибки подключения к БД

```bash
# Проверьте, что PostgreSQL запущен
sudo systemctl status postgresql

# Проверьте подключение
sudo -u postgres psql -d traffk_db

# Проверьте DATABASE_URL в .env
```

### Проблемы с правами

```bash
# Убедитесь, что пользователь traffk владеет файлами
sudo chown -R traffk:traffk /opt/traffk

# Проверьте права на .env
sudo chmod 600 /opt/traffk/.env
```

## 📈 Мониторинг

### Настройка мониторинга (опционально)

Можно использовать:
- **Sentry** - для отслеживания ошибок (указать SENTRY_DSN в .env)
- **Prometheus** - для метрик
- **Grafana** - для визуализации

## 🔄 Обновление

```bash
# Остановите бота
sudo systemctl stop traffk-bot

# Перейдите в директорию проекта
cd /opt/traffk  # или /home/traffk/traffk

# Обновите код (если используете git)
git pull

# Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt

# Примените миграции
alembic upgrade head

# Запустите бота
sudo systemctl start traffk-bot
```

## 📝 Полезные команды

```bash
# Просмотр использования ресурсов
htop

# Просмотр дискового пространства
df -h

# Просмотр сетевых подключений
netstat -tulpn

# Просмотр процессов Python
ps aux | grep python
```

---

**Готово!** Ваш бот должен быть запущен и работать на VPS. 🎉
