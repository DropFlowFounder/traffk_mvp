"""
Главный файл бота Traffk MVP
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import engine, Base
from handlers import common, tasks, tasks_list, proof, finance, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def main():
    """Главная функция запуска бота"""
    # Проверка токена
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN not set in environment variables!")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(tasks_list.router)
    dp.include_router(proof.router)
    dp.include_router(finance.router)
    dp.include_router(admin.router)
    
    # Инициализация БД
    await init_db()
    
    logger.info("Bot started")
    
    # Запуск бота
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error in polling: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Создаем директорию для логов
    import os
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
