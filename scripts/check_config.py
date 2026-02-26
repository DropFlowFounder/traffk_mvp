#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед запуском
"""
import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы можно было импортировать
# модули уровня проекта (config, database, models) при запуске скрипта
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def check_env_file():
    """Проверка наличия .env файла"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("   Создайте его на основе .env.example:")
        print("   cp .env.example .env")
        return False
    
    print("✅ Файл .env найден")
    return True

def check_env_variables():
    """Проверка обязательных переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "BOT_TOKEN": "Токен бота от @BotFather",
        "DATABASE_URL": "Строка подключения к PostgreSQL",
        "ADMIN_IDS": "Telegram ID администраторов (через запятую)"
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  - {var}: {description}")
        else:
            # Маскируем чувствительные данные
            if var == "BOT_TOKEN":
                masked = value[:10] + "..." if len(value) > 10 else "***"
            elif var == "DATABASE_URL":
                # Маскируем пароль в URL
                if "@" in value:
                    parts = value.split("@")
                    if ":" in parts[0]:
                        user_pass = parts[0].split(":")
                        masked = f"{user_pass[0]}:***@{parts[1]}"
                    else:
                        masked = value
                else:
                    masked = value
            else:
                masked = value
            print(f"✅ {var}: {masked}")
    
    if missing:
        print("\n❌ Отсутствуют обязательные переменные:")
        for var in missing:
            print(var)
        return False
    
    return True

def check_database_connection():
    """Проверка подключения к базе данных"""
    try:
        from config import settings
        from sqlalchemy import text
        from database import engine
        
        import asyncio
        
        async def test_connection():
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return True
            except Exception as e:
                print(f"❌ Ошибка подключения к БД: {e}")
                return False
        
        result = asyncio.run(test_connection())
        if result:
            print("✅ Подключение к базе данных успешно")
        return result
    except Exception as e:
        print(f"⚠️  Не удалось проверить подключение к БД: {e}")
        print("   Убедитесь, что PostgreSQL запущен и DATABASE_URL корректен")
        return False

def check_admin_ids():
    """Проверка формата ADMIN_IDS"""
    try:
        from config import settings
        admin_ids = settings.admin_ids_list
        
        if not admin_ids:
            print("⚠️  ADMIN_IDS пуст или некорректен")
            print("   Убедитесь, что указаны Telegram ID администраторов")
            return False
        
        print(f"✅ Найдено администраторов: {len(admin_ids)}")
        for admin_id in admin_ids:
            print(f"   - {admin_id}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке ADMIN_IDS: {e}")
        return False

def main():
    """Главная функция проверки"""
    print("🔍 Проверка конфигурации Traffk MVP...\n")
    
    checks = [
        ("Файл .env", check_env_file),
        ("Переменные окружения", check_env_variables),
        ("ADMIN_IDS", check_admin_ids),
        ("Подключение к БД", check_database_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    if all(results):
        print("✅ Все проверки пройдены! Бот готов к запуску.")
        return 0
    else:
        print("❌ Некоторые проверки не пройдены. Исправьте ошибки перед запуском.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
