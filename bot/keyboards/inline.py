from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import Supplement
from bot.utils.timezone import COMMON_TIMEZONES


def reminder_keyboard(log_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Принял", callback_data=f"taken:{log_id}"),
        InlineKeyboardButton(text="❌ Пропустить", callback_data=f"skip:{log_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="⏰ +30 мин", callback_data=f"snooze_30:{log_id}"),
        InlineKeyboardButton(text="⏰ +1 час", callback_data=f"snooze_60:{log_id}"),
    )
    return builder.as_markup()


def timezone_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, tz in COMMON_TIMEZONES:
        builder.button(text=label, callback_data=f"tz:{tz}")
    builder.adjust(1)
    return builder.as_markup()


def supplements_list_keyboard(supplements: list[Supplement]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sup in supplements:
        builder.button(text=f"🗑 {sup.name}", callback_data=f"del_supplement:{sup.id}")
    builder.adjust(1)
    return builder.as_markup()


def stats_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 За неделю", callback_data="stats_week"),
        InlineKeyboardButton(text="📅 За месяц", callback_data="stats_month"),
    )
    return builder.as_markup()


def confirm_delete_keyboard(supplement_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Удалить", callback_data=f"confirm_del:{supplement_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_del"),
    )
    return builder.as_markup()


def stock_update_keyboard(supplements: list[Supplement]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sup in supplements:
        builder.button(text=sup.name, callback_data=f"update_stock:{sup.id}")
    builder.adjust(1)
    return builder.as_markup()


def low_stock_keyboard(supplement_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Заказал, обновить запас", callback_data=f"reorder_done:{supplement_id}")
    return builder.as_markup()
