"""
Inline-клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models import UserRole, TaskStatus


def get_role_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📢 Рекламодатель", callback_data="role_advertiser"))
    builder.add(InlineKeyboardButton(text="🚀 Исполнитель", callback_data="role_traffic"))
    builder.add(InlineKeyboardButton(text="🔄 Обе роли", callback_data="role_both"))
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    """Главное меню в зависимости от роли"""
    builder = InlineKeyboardBuilder()
    
    if role in [UserRole.ADVERTISER, UserRole.BOTH]:
        builder.add(InlineKeyboardButton(text="➕ Создать задание", callback_data="create_task"))
        builder.add(InlineKeyboardButton(text="📋 Мои задания", callback_data="my_tasks"))
    
    if role in [UserRole.TRAFFIC, UserRole.BOTH]:
        builder.add(InlineKeyboardButton(text="📰 Лента заданий", callback_data="tasks_list"))
    
    builder.add(InlineKeyboardButton(text="💰 Баланс", callback_data="balance"))
    builder.add(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    builder.add(InlineKeyboardButton(text="❓ Помощь", callback_data="help"))
    builder.adjust(2)
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int, status: TaskStatus, user_is_advertiser: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с заданием"""
    builder = InlineKeyboardBuilder()
    
    if status == TaskStatus.DRAFT and user_is_advertiser:
        builder.add(InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_task_{task_id}"))
        builder.add(InlineKeyboardButton(text="📤 Опубликовать", callback_data=f"publish_task_{task_id}"))
        builder.add(InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_task_{task_id}"))
    elif status == TaskStatus.PUBLISHED and not user_is_advertiser:
        builder.add(InlineKeyboardButton(text="✅ Взять в работу", callback_data=f"take_task_{task_id}"))
    elif status == TaskStatus.TAKEN:
        if user_is_advertiser:
            builder.add(InlineKeyboardButton(text="👀 Проверить", callback_data=f"view_task_{task_id}"))
        else:
            builder.add(InlineKeyboardButton(text="📤 Отправить proof", callback_data=f"submit_proof_{task_id}"))
    elif status == TaskStatus.SUBMITTED and user_is_advertiser:
        builder.add(InlineKeyboardButton(text="✅ Принять", callback_data=f"confirm_task_{task_id}"))
        builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_task_{task_id}"))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="tasks_list"))
    builder.adjust(2)
    return builder.as_markup()


def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"))
    builder.add(InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}_{item_id}"))
    builder.adjust(2)
    return builder.as_markup()


def get_dispute_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для открытия спора"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⚖️ Открыть спор", callback_data=f"open_dispute_{task_id}"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_task_{task_id}"))
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💳 Депозиты", callback_data="admin_deposits"))
    builder.add(InlineKeyboardButton(text="💸 Выплаты", callback_data="admin_payouts"))
    builder.add(InlineKeyboardButton(text="⚖️ Споры", callback_data="admin_disputes"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.adjust(2)
    return builder.as_markup()


def get_admin_action_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий админа"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_approve_{action}_{item_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{action}_{item_id}"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_{action}"))
    builder.adjust(2)
    return builder.as_markup()


def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    builder = InlineKeyboardBuilder()
    
    if page > 1:
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    if page < total_pages:
        builder.add(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}_page_{page+1}"))
    
    builder.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()
