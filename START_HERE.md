# 🚀 Начните отсюда!

## Быстрая настройка локально

1. **Настройте переменные окружения:**
```bash
./setup_local.sh
```

Или вручную:
```bash
cp .env.example .env
nano .env  # Отредактируйте файл
```

2. **Проверьте конфигурацию:**
```bash
python3 scripts/check_config.py
```

3. **Установите зависимости:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Настройте базу данных:**
```bash
# Создайте БД PostgreSQL
createdb traffk_db

# Примените миграции
alembic upgrade head
```

5. **Запустите бота:**
```bash
python bot.py
```

## Развертывание на VPS

### Вариант 1: Автоматический (рекомендуется)

1. **Подготовьте архив:**
```bash
tar --exclude='.git' --exclude='__pycache__' --exclude='venv' --exclude='.env' -czf traffk-deploy.tar.gz .
```

2. **Загрузите на VPS:**
```bash
scp traffk-deploy.tar.gz user@your-vps-ip:/tmp/
```

3. **На VPS запустите:**
```bash
ssh user@your-vps-ip
cd /tmp
tar -xzf traffk-deploy.tar.gz
cd Traffk_mvp_beta_ai_cursor
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

4. **Настройте .env:**
```bash
sudo nano /opt/traffk/.env
# Укажите BOT_TOKEN и ADMIN_IDS
```

5. **Запустите:**
```bash
sudo systemctl start traffk-bot
sudo systemctl status traffk-bot
```

### Вариант 2: Через Git

См. [VPS_DEPLOY.md](VPS_DEPLOY.md) для подробных инструкций.

## 📚 Документация

- **QUICKSTART.md** - Быстрый старт
- **README.md** - Полная документация
- **DEPLOYMENT.md** - Подробное руководство по развертыванию
- **VPS_DEPLOY.md** - Быстрое развертывание на VPS

## 🔧 Полезные команды

```bash
# Проверка конфигурации
python3 scripts/check_config.py

# Просмотр логов (на VPS)
sudo journalctl -u traffk-bot -f

# Перезапуск (на VPS)
sudo systemctl restart traffk-bot
```

## ❓ Нужна помощь?

1. Проверьте логи: `logs/bot.log` (локально) или `sudo journalctl -u traffk-bot` (VPS)
2. Запустите проверку конфигурации: `python3 scripts/check_config.py`
3. См. раздел "Решение проблем" в README.md

---

**Готово к запуску!** 🎉
