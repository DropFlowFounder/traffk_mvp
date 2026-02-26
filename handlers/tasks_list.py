"""
Handlers для ленты заданий и взятия в работу
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from math import ceil

from database import get_session
from models import User, Task, TaskStatus, UserRole
from keyboards import (
    get_main_menu_keyboard, get_task_actions_keyboard,
    get_confirmation_keyboard, get_pagination_keyboard
)
from utils import get_or_create_user, format_task_status
from config import settings

router = Router()

TASKS_PER_PAGE = 5


@router.callback_query(F.data == "tasks_list")
async def show_tasks_list(callback: CallbackQuery, session: AsyncSession, page: int = 1):
    """Показать ленту заданий"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user or user.role not in [UserRole.TRAFFIC, UserRole.BOTH]:
        await callback.answer("Только исполнители могут просматривать задания", show_alert=True)
        return
    
    # Получаем опубликованные задания
    tasks_result = await session.execute(
        select(Task)
        .where(Task.status == TaskStatus.PUBLISHED)
        .order_by(Task.created_at.desc())
        .offset((page - 1) * TASKS_PER_PAGE)
        .limit(TASKS_PER_PAGE)
    )
    tasks = tasks_result.scalars().all()
    
    # Подсчет общего количества
    count_result = await session.execute(
        select(func.count(Task.id)).where(Task.status == TaskStatus.PUBLISHED)
    )
    total_tasks = count_result.scalar()
    total_pages = ceil(total_tasks / TASKS_PER_PAGE) if total_tasks > 0 else 1
    
    if not tasks:
        await callback.message.edit_text(
            "📰 Лента заданий\n\n"
            "Пока нет доступных заданий.\n"
            "Проверьте позже!",
            reply_markup=get_main_menu_keyboard(user.role)
        )
        await callback.answer()
        return
    
    # Формируем список заданий
    text = f"📰 Лента заданий (страница {page}/{total_pages})\n\n"
    for task in tasks:
        advertiser_result = await session.execute(
            select(User).where(User.id == task.advertiser_id)
        )
        advertiser = advertiser_result.scalar_one_or_none()
        advertiser_name = f"@{advertiser.username}" if advertiser and advertiser.username else f"ID:{advertiser.id}"
        
        text += (
            f"📋 #{task.id} - {task.title}\n"
            f"💰 {task.price:.2f} ₽ | ⏰ {task.deadline_days} дн.\n"
            f"👤 {advertiser_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    
    # Кнопки для каждого задания
    builder = InlineKeyboardBuilder()
    
    for task in tasks:
        builder.add(InlineKeyboardButton(
            text=f"📋 #{task.id} - {task.price:.2f} ₽",
            callback_data=f"view_public_task_{task.id}"
        ))
    
    builder.adjust(1)
    
    # Пагинация
    if total_pages > 1:
        pagination = get_pagination_keyboard(page, total_pages, "tasks_list")
        builder.attach(pagination)
    else:
        builder.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("tasks_list_page_"))
async def tasks_list_page(callback: CallbackQuery, session: AsyncSession):
    """Обработка пагинации ленты"""
    page = int(callback.data.split("_")[-1])
    await show_tasks_list(callback, session, page)


@router.callback_query(F.data.startswith("view_public_task_"))
async def view_public_task(callback: CallbackQuery, session: AsyncSession):
    """Просмотр публичного задания"""
    task_id = int(callback.data.split("_")[-1])
    
    task = await session.get(Task, task_id)
    if not task or task.status != TaskStatus.PUBLISHED:
        await callback.answer("Задание не найдено или недоступно", show_alert=True)
        return
    
    advertiser_result = await session.execute(
        select(User).where(User.id == task.advertiser_id)
    )
    advertiser = advertiser_result.scalar_one_or_none()
    
    text = (
        f"📋 Задание #{task.id}\n\n"
        f"📌 {task.title}\n"
        f"📝 {task.description}\n"
        f"🔗 {task.link or 'не указана'}\n"
        f"💰 {task.price:.2f} ₽\n"
        f"⏰ Срок: {task.deadline_days} дней\n"
        f"👤 Рекламодатель: @{advertiser.username if advertiser and advertiser.username else 'не указан'}\n"
        f"⭐ Репутация: {advertiser.reputation if advertiser else 0}\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_actions_keyboard(task.id, task.status, False)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("take_task_"))
async def take_task(callback: CallbackQuery, session: AsyncSession):
    """Взять задание в работу"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user or user.role not in [UserRole.TRAFFIC, UserRole.BOTH]:
        await callback.answer("Только исполнители могут брать задания", show_alert=True)
        return
    
    task = await session.get(Task, task_id)
    if not task:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    
    if task.status != TaskStatus.PUBLISHED:
        await callback.answer("Задание уже взято в работу или недоступно", show_alert=True)
        return
    
    if task.advertiser_id == user.id:
        await callback.answer("Нельзя взять своё задание", show_alert=True)
        return
    
    # Подтверждение
    await callback.message.edit_text(
        f"⚠️ Подтверждение\n\n"
        f"Вы хотите взять задание #{task_id} в работу?\n\n"
        f"После подтверждения задание будет заблокировано для других исполнителей.",
        reply_markup=get_confirmation_keyboard("take", task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_take_"))
async def confirm_take_task(callback: CallbackQuery, session: AsyncSession):
    """Подтверждение взятия задания"""
    task_id = int(callback.data.split("_")[-1])
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    task = await session.get(Task, task_id)
    if not task or task.status != TaskStatus.PUBLISHED:
        await callback.answer("Задание недоступно", show_alert=True)
        return
    
    # Назначаем исполнителя
    task.executor_id = user.id
    task.status = TaskStatus.TAKEN
    task.taken_at = datetime.utcnow()
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
                f"✅ Ваше задание #{task_id} взято в работу!\n\n"
                f"Исполнитель: @{user.username or 'не указан'}\n"
                f"Следите за выполнением."
            )
        except Exception as e:
            logger.error(f"Failed to send task taken notification: {e}")
    
    await callback.message.edit_text(
        f"✅ Задание #{task_id} взято в работу!\n\n"
        f"Теперь вы можете выполнить его и отправить proof."
    )
    await callback.answer("Задание взято в работу")
