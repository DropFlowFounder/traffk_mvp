"""
Handlers для финансовых операций
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from database import get_session
from models import User, Transaction, TransactionType, TransactionStatus
from keyboards import get_main_menu_keyboard
from utils import get_or_create_user, format_balance, format_transaction_status
from config import settings

router = Router()


@router.callback_query(F.data == "balance")
@router.message(Command("balance"))
async def show_balance(callback_or_message: CallbackQuery | Message, session: AsyncSession):
    """Показать баланс"""
    if isinstance(callback_or_message, CallbackQuery):
        user_id = callback_or_message.from_user.id
        message = callback_or_message.message
    else:
        user_id = callback_or_message.from_user.id
        message = callback_or_message
    
    result = await session.execute(
        select(User).where(User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = await get_or_create_user(session, user_id, message.from_user.username)
    
    text = (
        f"💰 Баланс\n\n"
        f"Текущий баланс: {format_balance(user.balance)}\n\n"
        f"Доступные действия:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit"))
    builder.add(InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw"))
    builder.add(InlineKeyboardButton(text="📜 История", callback_data="transactions"))
    builder.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=builder.as_markup())
        await callback_or_message.answer()
    else:
        await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "deposit")
@router.message(Command("deposit"))
async def show_deposit_info(callback_or_message: CallbackQuery | Message, session: AsyncSession):
    """Информация о пополнении"""
    if isinstance(callback_or_message, CallbackQuery):
        user_id = callback_or_message.from_user.id
        message = callback_or_message.message
    else:
        user_id = callback_or_message.from_user.id
        message = callback_or_message
    
    result = await session.execute(
        select(User).where(User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = await get_or_create_user(session, user_id, message.from_user.username)
    
    # Генерируем уникальный комментарий для идентификации платежа
    unique_code = f"DEP{user.id}{user.telegram_id}"
    
    text = (
        f"💳 Пополнение баланса\n\n"
        f"Для пополнения баланса переведите средства на:\n\n"
        f"📱 СБП: +7XXXXXXXXXX\n"
        f"💳 Карта: XXXX XXXX XXXX XXXX\n\n"
        f"⚠️ ВАЖНО: В комментарии к переводу укажите:\n"
        f"<code>{unique_code}</code>\n\n"
        f"После перевода администратор подтвердит депозит вручную.\n"
        f"Обычно это занимает до 24 часов.\n\n"
        f"Ваш ID для идентификации: {user.telegram_id}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📜 Мои депозиты", callback_data="my_deposits"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="balance"))
    
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback_or_message.answer()
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "withdraw")
@router.message(Command("withdraw"))
async def show_withdraw_info(callback_or_message: CallbackQuery | Message, session: AsyncSession):
    """Информация о выводе"""
    if isinstance(callback_or_message, CallbackQuery):
        user_id = callback_or_message.from_user.id
        message = callback_or_message.message
    else:
        user_id = callback_or_message.from_user.id
        message = callback_or_message
    
    result = await session.execute(
        select(User).where(User.telegram_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = await get_or_create_user(session, user_id, message.from_user.username)
    
    if user.balance <= 0:
        text = "❌ На балансе нет средств для вывода."
    else:
        text = (
            f"💸 Вывод средств\n\n"
            f"Доступно к выводу: {format_balance(user.balance)}\n\n"
            f"Для вывода средств отправьте реквизиты:\n"
            f"• СБП (номер телефона)\n"
            f"• Или номер карты\n\n"
            f"Администратор обработает запрос вручную."
        )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    
    class WithdrawStates(StatesGroup):
        details = State()
    
    if user.balance > 0:
        await message.answer(
            "Отправьте реквизиты для вывода (СБП или номер карты):"
        )
        # Здесь нужно использовать FSM для обработки реквизитов
        # Упрощенная версия - просто создаем транзакцию
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📜 Мои выплаты", callback_data="my_payouts"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="balance"))
    
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=builder.as_markup())
        await callback_or_message.answer()
    else:
        await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "transactions")
async def show_transactions(callback: CallbackQuery, session: AsyncSession):
    """Показать историю транзакций"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    transactions_result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
    )
    transactions = transactions_result.scalars().all()
    
    if not transactions:
        text = "📜 История транзакций\n\nУ вас пока нет транзакций."
    else:
        text = "📜 История транзакций\n\n"
        type_emojis = {
            TransactionType.DEPOSIT: "💳",
            TransactionType.PAYOUT: "💸",
            TransactionType.COMMISSION: "📊",
            TransactionType.REFUND: "↩️"
        }
        
        for trans in transactions:
            emoji = type_emojis.get(trans.type, "💰")
            text += (
                f"{emoji} {trans.type.value.upper()}: "
                f"{format_balance(trans.amount)} - "
                f"{format_transaction_status(trans.status)}\n"
                f"📅 {trans.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="balance"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
