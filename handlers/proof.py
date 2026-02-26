"""
Handlers для proof и подтверждения заданий
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from database import get_session
from models import User, Task, TaskStatus
from keyboards import (
    get_main_menu_keyboard, get_task_actions_keyboard,
    get_confirmation_keyboard, get_dispute_keyboard
)
from utils import get_or_create_user
from config import settings

router = Router()


class ProofStates(StatesGroup):
    """Состояния для загрузки proof"""
    text = State()
    photos = State()


@router.callback_query(F.data.startswith("submit_proof_"))
async def start_submit_proof(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать загрузку proof"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    task = await session.get(Task, task_id)
    if not task:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    
    if task.executor_id != user.id:
        await callback.answer("Это не ваше задание", show_alert=True)
        return
    
    if task.status != TaskStatus.TAKEN:
        await callback.answer("Задание не в работе", show_alert=True)
        return
    
    await state.update_data(task_id=task_id, photos=[])
    await state.set_state(ProofStates.text)
    
    await callback.message.edit_text(
        f"📤 Отправка proof для задания #{task_id}\n\n"
        "Введите текстовый отчёт о выполнении:"
    )
    await callback.answer()


@router.message(StateFilter(ProofStates.text))
async def process_proof_text(message: Message, state: FSMContext):
    """Обработка текста proof"""
    await state.update_data(proof_text=message.text)
    await state.set_state(ProofStates.photos)
    
    await message.answer(
        f"Теперь отправьте до {settings.MAX_PROOF_PHOTOS} фотографий как доказательство.\n"
        "Или отправьте '-' чтобы пропустить."
    )


@router.message(StateFilter(ProofStates.photos), F.photo)
async def process_proof_photo(message: Message, state: FSMContext):
    """Обработка фото proof"""
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if len(photos) >= settings.MAX_PROOF_PHOTOS:
        await message.answer(f"Максимум {settings.MAX_PROOF_PHOTOS} фотографий")
        return
    
    # Сохраняем file_id
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    
    remaining = settings.MAX_PROOF_PHOTOS - len(photos)
    if remaining > 0:
        await message.answer(f"Фото добавлено. Осталось мест: {remaining}. Отправьте ещё или '-' для завершения.")
    else:
        await message.answer("Достигнут лимит фотографий. Отправляю proof...")
        await submit_proof_final(message, state)


@router.message(StateFilter(ProofStates.photos))
async def process_proof_finish(message: Message, state: FSMContext):
    """Завершение загрузки proof"""
    if message.text == "-":
        await submit_proof_final(message, state)
    else:
        await message.answer("Отправьте фотографию или '-' для завершения")


async def submit_proof_final(message: Message, state: FSMContext):
    """Финальная отправка proof"""
    async with async_session_maker() as session:
        data = await state.get_data()
        task_id = data["task_id"]
        
        task = await session.get(Task, task_id)
        if not task:
            await message.answer("Ошибка: задание не найдено")
            await state.clear()
            return
        
        task.proof_text = data.get("proof_text", "")
        task.proof_photos = json.dumps(data.get("photos", []))
        task.status = TaskStatus.SUBMITTED
        task.submitted_at = datetime.utcnow()
        
        await session.commit()
        
        # Уведомляем рекламодателя
        advertiser_result = await session.execute(
            select(User).where(User.id == task.advertiser_id)
        )
        advertiser = advertiser_result.scalar_one_or_none()
        
        if advertiser:
            try:
                bot = Bot.get_current()
                await bot.send_message(
                    advertiser.telegram_id,
                    f"📤 Получен proof для задания #{task_id}!\n\n"
                    f"Проверьте выполнение и подтвердите или отклоните."
                )
            except Exception as e:
                logger.error(f"Failed to send proof notification: {e}")
        
        await message.answer(
            f"✅ Proof отправлен для задания #{task_id}!\n\n"
            "Ожидайте подтверждения от рекламодателя."
        )
    
    await state.clear()


@router.callback_query(F.data.startswith("confirm_task_"))
async def confirm_task_completion(callback: CallbackQuery, session: AsyncSession):
    """Подтверждение выполнения задания"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    task = await session.get(Task, task_id)
    if not task or task.advertiser_id != user.id:
        await callback.answer("Ошибка доступа", show_alert=True)
        return
    
    if task.status != TaskStatus.SUBMITTED:
        await callback.answer("Задание не на проверке", show_alert=True)
        return
    
    # Подтверждаем задание
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    
    # Создаем транзакцию на выплату исполнителю
    from decimal import Decimal
    
    executor = await session.get(User, task.executor_id)
    if executor:
        # Выплата исполнителю (95% после комиссии)
        payout_amount = task.price * Decimal("0.95")
        commission_amount = task.price * Decimal(str(settings.COMMISSION_RATE))
        
        # Создаем транзакции
        payout_transaction = Transaction(
            user_id=executor.id,
            task_id=task.id,
            type=TransactionType.PAYOUT,
            amount=payout_amount,
            status=TransactionStatus.PENDING
        )
        
        commission_transaction = Transaction(
            user_id=user.id,  # Комиссия списывается с рекламодателя
            task_id=task.id,
            type=TransactionType.COMMISSION,
            amount=commission_amount,
            status=TransactionStatus.CONFIRMED  # Комиссия сразу подтверждена
        )
        
        session.add(payout_transaction)
        session.add(commission_transaction)
        
        # Уведомляем админа о необходимости выплаты
        for admin_id in settings.admin_ids_list:
            try:
                bot = Bot.get_current()
                await bot.send_message(
                    admin_id,
                    f"💰 Требуется выплата\n\n"
                    f"Задание: #{task_id}\n"
                    f"Исполнитель: @{executor.username or 'не указан'}\n"
                    f"Сумма: {payout_amount:.2f} ₽\n"
                    f"Комиссия: {commission_amount:.2f} ₽\n\n"
                    f"Используйте /admin_payouts для обработки."
                )
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
    
    await session.commit()
    
    # Уведомляем исполнителя
    if executor:
        try:
            bot = Bot.get_current()
            await bot.send_message(
                executor.telegram_id,
                f"✅ Ваше задание #{task_id} подтверждено!\n\n"
                f"Выплата будет обработана администратором."
            )
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")
    
    await callback.message.edit_text(
        f"✅ Задание #{task_id} подтверждено!\n\n"
        "Исполнитель получит выплату после обработки администратором."
    )
    await callback.answer("Задание подтверждено")


@router.callback_query(F.data.startswith("reject_task_"))
async def reject_task(callback: CallbackQuery, session: AsyncSession):
    """Отклонение задания"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    task = await session.get(Task, task_id)
    if not task or task.advertiser_id != user.id:
        await callback.answer("Ошибка доступа", show_alert=True)
        return
    
    if task.status != TaskStatus.SUBMITTED:
        await callback.answer("Задание не на проверке", show_alert=True)
        return
    
    # Показываем опцию открыть спор
    await callback.message.edit_text(
        f"❌ Вы отклонили задание #{task_id}\n\n"
        "Если вы не согласны с результатом, можете открыть спор.\n"
        "Администратор рассмотрит ситуацию.",
        reply_markup=get_dispute_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("open_dispute_"))
async def open_dispute(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Открытие спора"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    task = await session.get(Task, task_id)
    if not task:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    
    # Проверяем, что задание в статусе submitted или уже отклонено
    if task.status not in [TaskStatus.SUBMITTED]:
        await callback.answer("Нельзя открыть спор для этого задания", show_alert=True)
        return
    
    await state.update_data(task_id=task_id)
    await state.set_state("dispute_reason")
    
    await callback.message.edit_text(
        f"⚖️ Открытие спора для задания #{task_id}\n\n"
        "Опишите причину спора и ваши претензии:"
    )
    await callback.answer()


@router.message(StateFilter("dispute_reason"))
async def process_dispute_reason(message: Message, state: FSMContext):
    """Обработка причины спора"""
    from models import Dispute, DisputeStatus
    
    async with async_session_maker() as session:
        data = await state.get_data()
        task_id = data["task_id"]
        
        task = await session.get(Task, task_id)
        if not task:
            await message.answer("Ошибка: задание не найдено")
            await state.clear()
            return
        
        # Создаем спор
        dispute = Dispute(
            task_id=task_id,
            opened_by=task.advertiser_id,  # Рекламодатель открывает спор
            reason=message.text,
            status=DisputeStatus.OPEN
        )
        session.add(dispute)
        
        task.status = TaskStatus.DISPUTED
        await session.commit()
        
        # Уведомляем админа
        for admin_id in settings.admin_ids_list:
            try:
                bot = Bot.get_current()
                await bot.send_message(
                    admin_id,
                    f"⚖️ Открыт спор\n\n"
                    f"Задание: #{task_id}\n"
                    f"Открыл: @{message.from_user.username or 'не указан'}\n"
                    f"Причина: {message.text}\n\n"
                    f"Используйте /admin_disputes для обработки."
                )
            except Exception as e:
                logger.error(f"Failed to send dispute notification: {e}")
        
        # Уведомляем исполнителя
        executor_result = await session.execute(
            select(User).where(User.id == task.executor_id)
        )
        executor = executor_result.scalar_one_or_none()
        
        if executor:
            try:
                bot = Bot.get_current()
                await bot.send_message(
                    executor.telegram_id,
                    f"⚖️ Открыт спор по заданию #{task_id}\n\n"
                    f"Администратор рассмотрит ситуацию."
                )
            except Exception as e:
                logger.error(f"Failed to send dispute notification to executor: {e}")
        
        await message.answer(
            f"⚖️ Спор открыт для задания #{task_id}!\n\n"
            "Администратор рассмотрит ситуацию и примет решение."
        )
    
    await state.clear()
