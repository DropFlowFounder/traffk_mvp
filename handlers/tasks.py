"""
Handlers для работы с заданиями
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from decimal import Decimal

from database import get_session
from models import User, Task, TaskStatus, UserRole
from keyboards import (
    get_main_menu_keyboard, get_task_actions_keyboard, 
    get_confirmation_keyboard, get_pagination_keyboard
)
from utils import get_or_create_user, format_task_status, format_balance
from config import settings

router = Router()


class CreateTaskStates(StatesGroup):
    """Состояния для создания задания"""
    title = State()
    description = State()
    link = State()
    price = State()
    deadline = State()
    confirm = State()


@router.callback_query(F.data == "create_task")
async def start_create_task(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать создание задания"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user or user.role not in [UserRole.ADVERTISER, UserRole.BOTH]:
        await callback.answer("Только рекламодатели могут создавать задания", show_alert=True)
        return
    
    await state.set_state(CreateTaskStates.title)
    await callback.message.edit_text(
        "📝 Создание задания\n\n"
        "Введите название задания (до 100 символов):"
    )
    await callback.answer()


@router.message(StateFilter(CreateTaskStates.title))
async def process_title(message: Message, state: FSMContext):
    """Обработка названия"""
    if len(message.text) > settings.MAX_TITLE_LENGTH:
        await message.answer(f"Название слишком длинное. Максимум {settings.MAX_TITLE_LENGTH} символов.")
        return
    
    await state.update_data(title=message.text)
    await state.set_state(CreateTaskStates.description)
    await message.answer(
        "Введите описание задания (до 1000 символов):"
    )


@router.message(StateFilter(CreateTaskStates.description))
async def process_description(message: Message, state: FSMContext):
    """Обработка описания"""
    if len(message.text) > settings.MAX_DESCRIPTION_LENGTH:
        await message.answer(f"Описание слишком длинное. Максимум {settings.MAX_DESCRIPTION_LENGTH} символов.")
        return
    
    await state.update_data(description=message.text)
    await state.set_state(CreateTaskStates.link)
    await message.answer(
        "Введите ссылку для перехода/установки (или отправьте '-' чтобы пропустить):"
    )


@router.message(StateFilter(CreateTaskStates.link))
async def process_link(message: Message, state: FSMContext):
    """Обработка ссылки"""
    link = message.text if message.text != "-" else None
    await state.update_data(link=link)
    await state.set_state(CreateTaskStates.price)
    await message.answer(
        f"Введите сумму задания (от {settings.MIN_TASK_PRICE:.0f} до {settings.MAX_TASK_PRICE:.0f} ₽):"
    )


@router.message(StateFilter(CreateTaskStates.price))
async def process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    try:
        price = Decimal(message.text.replace(",", "."))
        if price < settings.MIN_TASK_PRICE or price > settings.MAX_TASK_PRICE:
            await message.answer(
                f"Сумма должна быть от {settings.MIN_TASK_PRICE:.0f} до {settings.MAX_TASK_PRICE:.0f} ₽"
            )
            return
    except (ValueError, AttributeError):
        await message.answer("Введите корректную сумму (число)")
        return
    
    await state.update_data(price=price)
    await state.set_state(CreateTaskStates.deadline)
    await message.answer(
        f"Введите срок выполнения в днях (от {settings.MIN_DEADLINE_DAYS} до {settings.MAX_DEADLINE_DAYS}):"
    )


@router.message(StateFilter(CreateTaskStates.deadline))
async def process_deadline(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка дедлайна и подтверждение"""
    try:
        deadline = int(message.text)
        if deadline < settings.MIN_DEADLINE_DAYS or deadline > settings.MAX_DEADLINE_DAYS:
            await message.answer(
                f"Срок должен быть от {settings.MIN_DEADLINE_DAYS} до {settings.MAX_DEADLINE_DAYS} дней"
            )
            return
    except ValueError:
        await message.answer("Введите корректное число дней")
        return
    
    data = await state.get_data()
    
    # Проверка баланса
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if user.balance < data['price']:
        await message.answer(
            f"❌ Недостаточно средств на балансе.\n"
            f"Требуется: {data['price']:.2f} ₽\n"
            f"На балансе: {user.balance:.2f} ₽\n\n"
            "Пополните баланс через команду /deposit"
        )
        await state.clear()
        return
    
    await state.update_data(deadline=deadline)
    
    # Показываем превью
    preview = (
        f"📋 Превью задания:\n\n"
        f"📌 Название: {data['title']}\n"
        f"📝 Описание: {data['description']}\n"
        f"🔗 Ссылка: {data['link'] or 'не указана'}\n"
        f"💰 Сумма: {data['price']:.2f} ₽\n"
        f"⏰ Срок: {deadline} дней\n\n"
        f"Подтвердить создание?"
    )
    
    await message.answer(
        preview,
        reply_markup=get_confirmation_keyboard("create", 0)
    )
    await state.set_state(CreateTaskStates.confirm)


@router.callback_query(F.data.startswith("confirm_create_"))
async def confirm_create_task(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение создания задания"""
    data = await state.get_data()
    
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    # Создаем задание
    task = Task(
        advertiser_id=user.id,
        title=data['title'],
        description=data['description'],
        link=data.get('link'),
        price=data['price'],
        deadline_days=data['deadline'],
        status=TaskStatus.DRAFT
    )
    session.add(task)
    
    # Резервируем средства (списываем с баланса)
    user.balance -= data['price']
    
    await session.commit()
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ Задание создано!\n\n"
        f"ID задания: {task.id}\n"
        f"Статус: {format_task_status(TaskStatus.DRAFT)}\n\n"
        "Опубликуйте задание, чтобы исполнители могли его увидеть."
    )
    await callback.answer()


@router.callback_query(F.data == "my_tasks")
async def show_my_tasks(callback: CallbackQuery, session: AsyncSession):
    """Показать мои задания"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    tasks_result = await session.execute(
        select(Task).where(Task.advertiser_id == user.id).order_by(Task.created_at.desc())
    )
    tasks = tasks_result.scalars().all()
    
    if not tasks:
        await callback.message.edit_text(
            "📋 У вас пока нет заданий.\n\nСоздайте первое задание!",
            reply_markup=get_main_menu_keyboard(user.role)
        )
        await callback.answer()
        return
    
    # Показываем первое задание
    await show_task_details(callback, tasks[0].id, session, user)


@router.callback_query(F.data.startswith("view_task_"))
async def view_task(callback: CallbackQuery, session: AsyncSession):
    """Просмотр задания"""
    task_id = int(callback.data.split("_")[-1])
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    await show_task_details(callback, task_id, session, user)


async def show_task_details(callback: CallbackQuery, task_id: int, session: AsyncSession, user: User):
    """Показать детали задания"""
    task = await session.get(Task, task_id)
    if not task:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    
    is_advertiser = task.advertiser_id == user.id
    
    text = (
        f"📋 Задание #{task.id}\n\n"
        f"📌 {task.title}\n"
        f"📝 {task.description}\n"
        f"🔗 {task.link or 'не указана'}\n"
        f"💰 {task.price:.2f} ₽\n"
        f"⏰ Срок: {task.deadline_days} дней\n"
        f"📊 Статус: {format_task_status(task.status)}\n"
    )
    
    if task.executor_id:
        executor_result = await session.execute(
            select(User).where(User.id == task.executor_id)
        )
        executor = executor_result.scalar_one_or_none()
        if executor:
            text += f"👤 Исполнитель: @{executor.username or 'не указан'}\n"
    
    if task.status == TaskStatus.SUBMITTED and task.proof_text:
        text += f"\n📤 Proof:\n{task.proof_text}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_actions_keyboard(task.id, task.status, is_advertiser)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("publish_task_"))
async def publish_task(callback: CallbackQuery, session: AsyncSession):
    """Опубликовать задание"""
    task_id = int(callback.data.split("_")[-1])
    task = await session.get(Task, task_id)
    
    if not task or task.status != TaskStatus.DRAFT:
        await callback.answer("Задание не может быть опубликовано", show_alert=True)
        return
    
    task.status = TaskStatus.PUBLISHED
    await session.commit()
    
    await callback.message.edit_text(
        f"✅ Задание #{task_id} опубликовано!\n\n"
        "Теперь исполнители могут взять его в работу."
    )
    await callback.answer("Задание опубликовано")
