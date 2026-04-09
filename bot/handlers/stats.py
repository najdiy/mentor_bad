from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo, SupplementRepo, IntakeLogRepo, StockRepo
from bot.keyboards.inline import stats_period_keyboard
from bot.utils.formatters import format_stats_message

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message) -> None:
    await message.answer(
        "📊 Выберите период:",
        reply_markup=stats_period_keyboard(),
    )


@router.callback_query(lambda c: c.data in ("stats_week", "stats_month"))
async def handle_stats_period(callback: CallbackQuery, session: AsyncSession) -> None:
    days = 7 if callback.data == "stats_week" else 30
    period_label = "7 дней" if days == 7 else "30 дней"

    user_repo = UserRepo(session)
    sup_repo = SupplementRepo(session)
    log_repo = IntakeLogRepo(session)
    stock_repo = StockRepo(session)

    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала напишите /start", show_alert=True)
        return

    stats_rows = await log_repo.get_stats_for_period(user.id, days)
    supplements = await sup_repo.get_active_by_user(user.id)
    stocks = await stock_repo.get_by_user(user.id)

    sup_map = {s.id: s for s in supplements}
    stock_map = {s.supplement_id: s for s in stocks}

    text = format_stats_message(period_label, stats_rows, sup_map, stock_map)
    await callback.message.edit_text(text)
    await callback.answer()
