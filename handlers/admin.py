"""
Handlers для админ-панели
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import datetime

from database import get_session
from models import User, Task, Transaction, TransactionType, TransactionStatus, Dispute, DisputeStatus
from keyboards import get_admin_keyboard, get_admin_action_keyboard, get_confirmation_keyboard
from utils import is_admin, format_balance, format_transaction_status, format_task_status
from config import settings

router = Router()


def admin_required(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(*args, **kwargs):
        callback_or_message = args[0] if args else kwargs.get('callback_or_message')
        user_id = callback_or_message.from_user.id if hasattr(callback_or_message, 'from_user') else None
        
        if not user_id or not is_admin(user_id):
            if isinstance(callback_or_message, CallbackQuery):
                await callback_or_message.answer("Доступ запрещён", show_alert=True)
            else:
                await callback_or_message.answer("Доступ запрещён")
            return
        
        return await func(*args, **kwargs)
    return wrapper


@router.message(Command("admin"))
@admin_required
async def admin_panel(message: Message, session: AsyncSession):
    """Админ-панель"""
    text = (
        "🔧 Админ-панель\n\n"
        "Выберите раздел для управления:"
    )
    
    await message.answer(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin_deposits")
@admin_required
async def admin_deposits(callback: CallbackQuery, session: AsyncSession):
    """Список депозитов на подтверждение"""
    deposits_result = await session.execute(
        select(Transaction)
        .where(
            Transaction.type == TransactionType.DEPOSIT,
            Transaction.status == TransactionStatus.PENDING
        )
        .order_by(Transaction.created_at.desc())
        .limit(20)
    )
    deposits = deposits_result.scalars().all()
    
    if not deposits:
        text = "💳 Депозиты\n\nНет ожидающих подтверждения депозитов."
    else:
        text = "💳 Депозиты на подтверждение\n\n"
        for dep in deposits:
            user_result = await session.execute(
                select(User).where(User.id == dep.user_id)
            )
            user = user_result.scalar_one_or_none()
            username = f"@{user.username}" if user and user.username else f"ID:{dep.user_id}"
            
            text += (
                f"💰 {format_balance(dep.amount)}\n"
                f"👤 {username}\n"
                f"📅 {dep.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"ID транзакции: {dep.id}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    for dep in deposits[:5]:  # Показываем первые 5
        builder.add(InlineKeyboardButton(
            text=f"💰 {format_balance(dep.amount)}",
            callback_data=f"admin_view_deposit_{dep.id}"
        ))
    builder.add(InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_deposit_"))
@admin_required
async def admin_view_deposit(callback: CallbackQuery, session: AsyncSession):
    """Просмотр депозита"""
    deposit_id = int(callback.data.split("_")[-1])
    
    deposit = await session.get(Transaction, deposit_id)
    if not deposit or deposit.type != TransactionType.DEPOSIT:
        await callback.answer("Депозит не найден", show_alert=True)
        return
    
    user_result = await session.execute(
        select(User).where(User.id == deposit.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    text = (
        f"💳 Депозит #{deposit.id}\n\n"
        f"👤 Пользователь: @{user.username if user and user.username else 'не указан'}\n"
        f"🆔 Telegram ID: {user.telegram_id if user else 'N/A'}\n"
        f"💰 Сумма: {format_balance(deposit.amount)}\n"
        f"📅 Дата: {deposit.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Статус: {format_transaction_status(deposit.status)}\n"
    )
    
    if deposit.admin_comment:
        text += f"💬 Комментарий: {deposit.admin_comment}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_action_keyboard("deposit", deposit_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_deposit_"))
@admin_required
async def admin_approve_deposit(callback: CallbackQuery, session: AsyncSession):
    """Подтвердить депозит"""
    deposit_id = int(callback.data.split("_")[-1])
    
    deposit = await session.get(Transaction, deposit_id)
    if not deposit or deposit.status != TransactionStatus.PENDING:
        await callback.answer("Депозит не найден или уже обработан", show_alert=True)
        return
    
    user = await session.get(User, deposit.user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    # Подтверждаем депозит
    deposit.status = TransactionStatus.CONFIRMED
    user.balance += deposit.amount
    
    await session.commit()
    
    # Уведомляем пользователя
    try:
        bot = Bot.get_current()
        await bot.send_message(
            user.telegram_id,
            f"✅ Ваш депозит подтверждён!\n\n"
            f"Сумма: {format_balance(deposit.amount)}\n"
            f"Текущий баланс: {format_balance(user.balance)}"
        )
    except Exception as e:
        logger.error(f"Failed to send deposit notification: {e}")
    
    await callback.message.edit_text(
        f"✅ Депозит #{deposit_id} подтверждён!\n\n"
        f"Баланс пользователя обновлён."
    )
    await callback.answer("Депозит подтверждён")


@router.callback_query(F.data.startswith("admin_reject_deposit_"))
@admin_required
async def admin_reject_deposit(callback: CallbackQuery, session: AsyncSession):
    """Отклонить депозит"""
    deposit_id = int(callback.data.split("_")[-1])
    
    deposit = await session.get(Transaction, deposit_id)
    if not deposit or deposit.status != TransactionStatus.PENDING:
        await callback.answer("Депозит не найден или уже обработан", show_alert=True)
        return
    
    # Здесь можно добавить FSM для ввода комментария
    # Упрощенная версия - просто отклоняем
    
    deposit.status = TransactionStatus.REJECTED
    await session.commit()
    
    user = await session.get(User, deposit.user_id)
    if user:
        try:
            bot = Bot.get_current()
            await bot.send_message(
                user.telegram_id,
                f"❌ Ваш депозит отклонён.\n\n"
                f"Сумма: {format_balance(deposit.amount)}\n"
                f"Обратитесь в поддержку для уточнения."
            )
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {e}")
    
    await callback.message.edit_text(f"❌ Депозит #{deposit_id} отклонён.")
    await callback.answer("Депозит отклонён")


@router.callback_query(F.data == "admin_payouts")
@admin_required
async def admin_payouts(callback: CallbackQuery, session: AsyncSession):
    """Список выплат на обработку"""
    payouts_result = await session.execute(
        select(Transaction)
        .where(
            Transaction.type == TransactionType.PAYOUT,
            Transaction.status == TransactionStatus.PENDING
        )
        .order_by(Transaction.created_at.desc())
        .limit(20)
    )
    payouts = payouts_result.scalars().all()
    
    if not payouts:
        text = "💸 Выплаты\n\nНет ожидающих обработки выплат."
    else:
        text = "💸 Выплаты на обработку\n\n"
        for payout in payouts:
            user_result = await session.execute(
                select(User).where(User.id == payout.user_id)
            )
            user = user_result.scalar_one_or_none()
            username = f"@{user.username}" if user and user.username else f"ID:{payout.user_id}"
            
            text += (
                f"💰 {format_balance(payout.amount)}\n"
                f"👤 {username}\n"
                f"📅 {payout.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"ID транзакции: {payout.id}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    for payout in payouts[:5]:
        builder.add(InlineKeyboardButton(
            text=f"💰 {format_balance(payout.amount)}",
            callback_data=f"admin_view_payout_{payout.id}"
        ))
    builder.add(InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_payout_"))
@admin_required
async def admin_approve_payout(callback: CallbackQuery, session: AsyncSession):
    """Подтвердить выплату"""
    payout_id = int(callback.data.split("_")[-1])
    
    payout = await session.get(Transaction, payout_id)
    if not payout or payout.status != TransactionStatus.PENDING:
        await callback.answer("Выплата не найдена или уже обработана", show_alert=True)
        return
    
    user = await session.get(User, payout.user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    # Подтверждаем выплату (средства уже были зарезервированы при создании транзакции)
    payout.status = TransactionStatus.CONFIRMED
    await session.commit()
    
    # Уведомляем пользователя
    try:
        bot = Bot.get_current()
        await bot.send_message(
            user.telegram_id,
            f"✅ Ваша выплата обработана!\n\n"
            f"Сумма: {format_balance(payout.amount)}\n"
            f"Средства будут переведены в ближайшее время."
        )
    except Exception as e:
        logger.error(f"Failed to send payout notification: {e}")
    
    await callback.message.edit_text(f"✅ Выплата #{payout_id} подтверждена!")
    await callback.answer("Выплата подтверждена")


@router.callback_query(F.data == "admin_disputes")
@admin_required
async def admin_disputes(callback: CallbackQuery, session: AsyncSession):
    """Список споров"""
    disputes_result = await session.execute(
        select(Dispute)
        .where(Dispute.status == DisputeStatus.OPEN)
        .order_by(Dispute.created_at.desc())
        .limit(20)
    )
    disputes = disputes_result.scalars().all()
    
    if not disputes:
        text = "⚖️ Споры\n\nНет открытых споров."
    else:
        text = "⚖️ Открытые споры\n\n"
        for dispute in disputes:
            task = await session.get(Task, dispute.task_id)
            opener = await session.get(User, dispute.opened_by)
            
            text += (
                f"📋 Задание: #{dispute.task_id}\n"
                f"👤 Открыл: @{opener.username if opener and opener.username else 'не указан'}\n"
                f"📅 {dispute.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    for dispute in disputes[:5]:
        builder.add(InlineKeyboardButton(
            text=f"⚖️ Спор #{dispute.id}",
            callback_data=f"admin_view_dispute_{dispute.id}"
        ))
    builder.add(InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
@admin_required
async def admin_stats(callback: CallbackQuery, session: AsyncSession):
    """Статистика"""
    # Общее количество пользователей
    users_count = await session.scalar(select(func.count(User.id)))
    
    # Общее количество заданий
    tasks_count = await session.scalar(select(func.count(Task.id)))
    
    # Завершенные задания
    completed_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED)
    )
    
    # Общий оборот (сумма всех завершенных заданий)
    total_volume = await session.scalar(
        select(func.sum(Task.price)).where(Task.status == TaskStatus.COMPLETED)
    ) or Decimal("0")
    
    # Комиссия (5% от оборота)
    total_commission = total_volume * Decimal(str(settings.COMMISSION_RATE))
    
    text = (
        f"📊 Статистика\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📋 Заданий: {tasks_count}\n"
        f"✅ Завершено: {completed_tasks}\n"
        f"💰 Оборот: {format_balance(total_volume)}\n"
        f"📊 Комиссия: {format_balance(total_commission)}\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin_panel")
@admin_required
async def admin_panel_callback(callback: CallbackQuery):
    """Админ-панель (callback)"""
    text = (
        "🔧 Админ-панель\n\n"
        "Выберите раздел для управления:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    await callback.answer()
