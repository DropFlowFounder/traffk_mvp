"""
Конфигурация приложения Traffk MVP
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://user:password@localhost:5432/traffk_db"
    )
    
    # Admin IDs (comma-separated)
    ADMIN_IDS: str = os.getenv("ADMIN_IDS", "")
    
    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Commission rate (5%)
    COMMISSION_RATE: float = 0.05
    
    # Task limits
    MIN_TASK_PRICE: float = 100.0
    MAX_TASK_PRICE: float = 50000.0
    MIN_DEADLINE_DAYS: int = 1
    MAX_DEADLINE_DAYS: int = 30
    
    # File limits
    MAX_PROOF_PHOTOS: int = 5
    MAX_TITLE_LENGTH: int = 100
    MAX_DESCRIPTION_LENGTH: int = 1000
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Преобразует строку ADMIN_IDS в список целых чисел"""
        if not self.ADMIN_IDS:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_IDS.split(",") if uid.strip().isdigit()]


settings = Settings()
