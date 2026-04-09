from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo, SupplementRepo, StockRepo
from bot.keyboards.inline import stock_update_keyboard
from bot.states.fsm import UpdateStockStates
from bot.utils.formatters import format_stock_message

router = Router()


@router.message(Command("stock"))
@router.message(F.text == "📦 Остатки")
async def cmd_stock(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepo(session)
    sup_repo = SupplementRepo(session)
    stock_repo = StockRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return

    supplements = await sup_repo.get_active_by_user(user.id)
    sup_map = {s.id: s for s in supplements}

    stocks = await stock_repo.get_by_user(user.id)
    stocks = [s for s in stocks if s.supplement_id in sup_map]

    text = format_stock_message(stocks, sup_map)
    await message.answer(text)


@router.message(Command("update_stock"))
async def cmd_update_stock(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_repo = UserRepo(session)
    sup_repo = SupplementRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return

    supplements = await sup_repo.get_active_by_user(user.id)
    if not supplements:
        await message.answer("У вас нет БАД. Добавьте через /add_supplement")
        return

    await message.answer(
        "Выберите БАД, чтобы обновить запас:",
        reply_markup=stock_update_keyboard(supplements),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("update_stock:"))
async def handle_update_stock_select(callback: CallbackQuery, state: FSMContext) -> None:
    supplement_id = int(callback.data.split(":")[1])
    await state.set_state(UpdateStockStates.waiting_new_count)
    await state.update_data(update_supplement_id=supplement_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("📦 Введите новое количество единиц в запасе (целое число):")
    await callback.answer()


@router.message(UpdateStockStates.waiting_new_count)
async def process_new_count(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = message.text.strip()
    if not text.isdigit() or int(text) < 0:
        await message.answer("Введите целое число (0 и более):")
        return

    data = await state.get_data()
    supplement_id = data.get("update_supplement_id")
    await state.clear()

    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)

    await stock_repo.update_count(supplement_id, int(text))
    sup = await sup_repo.get_by_id(supplement_id)
    name = sup.name if sup else f"БАД #{supplement_id}"

    await message.answer(f"✅ Запас <b>{name}</b> обновлён: <b>{text} шт.</b>")


@router.message(Command("my_schedule"))
@router.message(F.text == "📋 Расписание")
async def cmd_my_schedule(message: Message, session: AsyncSession) -> None:
    from bot.database.repositories import IntakeLogRepo
    user_repo = UserRepo(session)
    log_repo = IntakeLogRepo(session)
    sup_repo = SupplementRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return

    logs = await log_repo.get_today_by_user(user.id)
    supplements = await sup_repo.get_active_by_user(user.id)
    sup_map = {s.id: s for s in supplements}

    from bot.utils.formatters import format_schedule_message
    text = format_schedule_message(logs, sup_map)
    await message.answer(text)
