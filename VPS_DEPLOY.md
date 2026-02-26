# 🚀 Быстрое развертывание на VPS

## Вариант 1: Автоматическое развертывание (рекомендуется)

### На вашем компьютере:

1. **Подготовьте проект:**
```bash
cd Traffk_mvp_beta_ai_cursor
./setup_local.sh  # Настройте переменные окружения локально для теста
```

2. **Создайте архив для VPS:**
```bash
# Создайте архив (исключая ненужные файлы)
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='logs/*.log' \
    -czf traffk-deploy.tar.gz .
```

3. **Загрузите на VPS:**
```bash
scp traffk-deploy.tar.gz user@your-vps-ip:/tmp/
```

### На VPS:

1. **Подключитесь к VPS:**
```bash
ssh user@your-vps-ip
```

2. **Распакуйте и запустите скрипт развертывания:**
```bash
cd /tmp
tar -xzf traffk-deploy.tar.gz
cd Traffk_mvp_beta_ai_cursor
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

3. **Настройте переменные окружения:**
```bash
sudo nano /opt/traffk/.env
```

Укажите:
- `BOT_TOKEN` - получите у @BotFather
- `DATABASE_URL` - будет создан автоматически, но проверьте пароль
- `ADMIN_IDS` - ваш Telegram ID (получите у @userinfobot)

4. **Запустите бота:**
```bash
sudo systemctl start traffk-bot
sudo systemctl status traffk-bot
```

## Вариант 2: Через Git (если проект в репозитории)

### На VPS:

```bash
# Установите зависимости
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git

# Создайте пользователя
sudo useradd -m -s /bin/bash traffk
sudo su - traffk

# Клонируйте репозиторий
git clone <your-repo-url> traffk
cd traffk

# Настройте окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
nano .env  # Укажите BOT_TOKEN, DATABASE_URL, ADMIN_IDS

# Настройте БД
exit  # Выйдите из пользователя traffk
sudo -u postgres psql
```

В psql:
```sql
CREATE DATABASE traffk_db;
CREATE USER traffk_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE traffk_db TO traffk_user;
\q
```

```bash
# Вернитесь к пользователю traffk
sudo su - traffk
cd traffk
source venv/bin/activate

# Примените миграции
alembic upgrade head

# Создайте systemd сервис
exit
sudo nano /etc/systemd/system/traffk-bot.service
```

Вставьте:
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

```bash
# Запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable traffk-bot
sudo systemctl start traffk-bot
sudo systemctl status traffk-bot
```

## 📊 Управление после развертывания

### Просмотр логов:
```bash
sudo journalctl -u traffk-bot -f
```

### Перезапуск:
```bash
sudo systemctl restart traffk-bot
```

### Остановка:
```bash
sudo systemctl stop traffk-bot
```

### Проверка статуса:
```bash
sudo systemctl status traffk-bot
```

## ✅ Проверка работы

1. Найдите бота в Telegram
2. Отправьте `/start`
3. Проверьте логи: `sudo journalctl -u traffk-bot -f`

## 🔒 Безопасность

### Настройте firewall:
```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

### Защитите .env файл:
```bash
sudo chmod 600 /opt/traffk/.env  # или /home/traffk/traffk/.env
```

## 📝 Полная документация

См. [DEPLOYMENT.md](DEPLOYMENT.md) для подробных инструкций.
