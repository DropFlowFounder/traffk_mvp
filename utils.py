"""
Вспомогательные функции
"""
from decimal import Decimal
from typing import Optional
from models import User, Task, Transaction, TransactionType, TransactionStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from config import settings


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str] = None) -> User:
    """Получить или создать пользователя"""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


async def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return telegram_id in settings.admin_ids_list


def format_balance(balance: Decimal) -> str:
    """Форматирование баланса"""
    return f"{balance:.2f} ₽"


def format_task_status(status) -> str:
    """Форматирование статуса задания"""
    status_emojis = {
        "draft": "📝 Черновик",
        "published": "📢 Опубликовано",
        "taken": "🔄 В работе",
        "submitted": "⏳ На проверке",
        "completed": "✅ Завершено",
        "cancelled": "❌ Отменено",
        "disputed": "⚖️ Спор"
    }
    return status_emojis.get(status.value if hasattr(status, 'value') else status, status)


def format_transaction_status(status) -> str:
    """Форматирование статуса транзакции"""
    status_emojis = {
        "pending": "⏳ Ожидает",
        "confirmed": "✅ Подтверждено",
        "rejected": "❌ Отклонено"
    }
    return status_emojis.get(status.value if hasattr(status, 'value') else status, status)


async def calculate_commission(amount: Decimal) -> Decimal:
    """Расчет комиссии (5%)"""
    return amount * Decimal(str(settings.COMMISSION_RATE))


async def create_transaction(
    session: AsyncSession,
    user_id: int,
    transaction_type: TransactionType,
    amount: Decimal,
    task_id: Optional[int] = None,
    status: TransactionStatus = TransactionStatus.PENDING
) -> Transaction:
    """Создать транзакцию"""
    transaction = Transaction(
        user_id=user_id,
        task_id=task_id,
        type=transaction_type,
        amount=amount,
        status=status
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


async def update_user_balance(session: AsyncSession, user_id: int, amount: Decimal) -> User:
    """Обновить баланс пользователя"""
    user = await session.get(User, user_id)
    if user:
        user.balance += amount
        await session.commit()
        await session.refresh(user)
    return user
