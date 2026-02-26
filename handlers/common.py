"""
Общие handlers (start, help, profile)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_session
from models import User, UserRole
from keyboards import get_role_keyboard, get_main_menu_keyboard
from utils import get_or_create_user, is_admin
from config import settings

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Обработчик команды /start"""
    user = await get_or_create_user(
        session, 
        message.from_user.id, 
        message.from_user.username
    )
    
    if not user.role:
        await message.answer(
            "👋 Добро пожаловать в Traffk!\n\n"
            "Выберите вашу роль:",
            reply_markup=get_role_keyboard()
        )
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(user.role)
        )


@router.callback_query(F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, session: AsyncSession):
    """Обработка выбора роли"""
    role_map = {
        "role_advertiser": UserRole.ADVERTISER,
        "role_traffic": UserRole.TRAFFIC,
        "role_both": UserRole.BOTH
    }
    
    role = role_map.get(callback.data)
    if not role:
        await callback.answer("Ошибка выбора роли", show_alert=True)
        return
    
    user = await get_or_create_user(
        session,
        callback.from_user.id,
        callback.from_user.username
    )
    user.role = role
    await session.commit()
    
    await callback.message.edit_text(
        f"✅ Роль установлена: {role.value}\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(role)
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, session: AsyncSession):
    """Главное меню"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.role:
        await callback.answer("Сначала выберите роль через /start", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(user.role)
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, session: AsyncSession):
    """Показать профиль"""
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    role_text = {
        UserRole.ADVERTISER: "📢 Рекламодатель",
        UserRole.TRAFFIC: "🚀 Исполнитель",
        UserRole.BOTH: "🔄 Обе роли"
    }
    
    text = (
        f"👤 Профиль\n\n"
        f"🆔 ID: {user.telegram_id}\n"
        f"👤 Username: @{user.username or 'не указан'}\n"
        f"🎭 Роль: {role_text.get(user.role, 'не выбрана')}\n"
        f"💰 Баланс: {user.balance:.2f} ₽\n"
        f"⭐ Репутация: {user.reputation}\n"
        f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard(user.role))
    await callback.answer()


@router.callback_query(F.data == "help")
@router.message(Command("help"))
async def show_help(callback_or_message: CallbackQuery | Message, session: AsyncSession):
    """Показать справку"""
    help_text = (
        "❓ Помощь по использованию бота\n\n"
        "📋 Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "📢 Для рекламодателей:\n"
        "• Создавайте задания на размещение трафика\n"
        "• Пополняйте баланс для оплаты заданий\n"
        "• Проверяйте выполненные работы\n"
        "• Подтверждайте или отклоняйте результаты\n\n"
        "🚀 Для исполнителей:\n"
        "• Просматривайте доступные задания\n"
        "• Берите задания в работу\n"
        "• Загружайте доказательства выполнения\n"
        "• Получайте выплаты после подтверждения\n\n"
        "💰 Финансы:\n"
        "• Все платежи проходят через ручное подтверждение администратора\n"
        "• Комиссия сервиса: 5% с каждой успешной сделки\n"
        "• Минимальная сумма задания: 100 ₽\n"
        "• Максимальная сумма задания: 50 000 ₽\n\n"
        "⚖️ Споры:\n"
        "• При возникновении разногласий можно открыть спор\n"
        "• Администратор рассмотрит спор и примет решение\n\n"
        "💬 По вопросам: @your_support_username"
    )
    
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(help_text, reply_markup=get_main_menu_keyboard(UserRole.BOTH))
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(help_text)
