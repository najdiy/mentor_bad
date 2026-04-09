from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Расписание"), KeyboardButton(text="💊 Мои БАД")],
            [KeyboardButton(text="📦 Остатки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="➕ Добавить БАД"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
