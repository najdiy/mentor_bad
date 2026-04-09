from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo
from bot.keyboards.reply import main_menu_keyboard
from bot.keyboards.inline import timezone_keyboard
from bot.utils.timezone import is_valid_timezone

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    repo = UserRepo(session)
    user, is_new = await repo.upsert(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if is_new:
        await message.answer(
            f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Я помогу вам не забывать принимать БАД от <b>Mentor Bads</b> 💊\n\n"
            "Для начала выберите ваш часовой пояс:",
            reply_markup=timezone_keyboard(),
        )
    else:
        await message.answer(
            f"👋 С возвращением, <b>{message.from_user.first_name}</b>!",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def handle_timezone_selection(callback: CallbackQuery, session: AsyncSession) -> None:
    tz = callback.data.split(":", 1)[1]
    if not is_valid_timezone(tz):
        await callback.answer("Неизвестный часовой пояс", show_alert=True)
        return

    repo = UserRepo(session)
    await repo.update_timezone(callback.from_user.id, tz)
    await callback.message.edit_text(
        f"✅ Часовой пояс установлен: <b>{tz}</b>\n\n"
        "Теперь добавьте ваш первый БАД через /add_supplement или выберите действие в меню:",
    )
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "💊 <b>Mentor Bads Bot — справка</b>\n\n"
        "/start — начать / главное меню\n"
        "/add_supplement — добавить новый БАД\n"
        "/supplements — список ваших БАД\n"
        "/my_schedule — расписание на сегодня\n"
        "/stock — остатки\n"
        "/update_stock — обновить запас\n"
        "/stats — статистика приёмов\n"
        "/timezone — сменить часовой пояс\n"
        "/pause — приостановить все напоминания\n"
        "/resume — возобновить напоминания\n"
        "/help — эта справка"
    )
    await message.answer(text)


@router.message(Command("timezone"))
async def cmd_timezone(message: Message) -> None:
    await message.answer(
        "🌍 Выберите ваш часовой пояс:",
        reply_markup=timezone_keyboard(),
    )


@router.message(lambda m: m.text == "⚙️ Настройки")
async def btn_settings(message: Message, session: AsyncSession) -> None:
    repo = UserRepo(session)
    user = await repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return
    await message.answer(
        f"⚙️ <b>Ваши настройки</b>\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🌍 Часовой пояс: {user.timezone}\n"
        f"🔔 Уведомления: {'включены' if user.is_active else 'приостановлены'}\n\n"
        "Для смены часового пояса: /timezone",
    )
