import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo, SupplementRepo, ScheduleRepo, StockRepo
from bot.keyboards.inline import supplements_list_keyboard, confirm_delete_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.scheduler.manager import add_reminder_job, add_stock_check_job, remove_jobs_for_supplement
from bot.states.fsm import AddSupplementStates

router = Router()

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


@router.message(Command("add_supplement"))
@router.message(F.text == "➕ Добавить БАД")
async def cmd_add_supplement(message: Message, state: FSMContext) -> None:
    await state.set_state(AddSupplementStates.waiting_name)
    await message.answer(
        "💊 <b>Добавление нового БАД</b>\n\n"
        "Введите название БАД (например: Omega-3 Mentor):",
    )


@router.message(AddSupplementStates.waiting_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 128:
        await message.answer("Название должно быть от 2 до 128 символов. Попробуйте ещё раз:")
        return
    await state.update_data(name=name)
    await state.set_state(AddSupplementStates.waiting_dose)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Сколько капсул/таблеток за один приём? (введите число, например: 1 или 2):"
    )


@router.message(AddSupplementStates.waiting_dose)
async def process_dose(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 20):
        await message.answer("Введите число от 1 до 20:")
        return
    await state.update_data(dose=int(text))
    await state.set_state(AddSupplementStates.waiting_times)
    await message.answer(
        "🕐 В какое время напоминать? Введите время в формате <b>ЧЧ:ММ</b>\n"
        "Можно добавить несколько — отправляйте по одному.\n"
        "Когда закончите — отправьте /done\n\n"
        "Пример: <code>08:00</code>"
    )


@router.message(AddSupplementStates.waiting_times, Command("done"))
async def process_times_done(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    times = data.get("times", [])
    if not times:
        await message.answer("Добавьте хотя бы одно время. Например: <code>08:00</code>")
        return
    await state.set_state(AddSupplementStates.waiting_stock_count)
    times_str = ", ".join(times)
    await message.answer(
        f"✅ Времена напоминаний: <b>{times_str}</b>\n\n"
        "📦 Сколько единиц (капсул/таблеток) у вас сейчас в запасе?"
    )


@router.message(AddSupplementStates.waiting_times)
async def process_time_entry(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    m = TIME_RE.match(text)
    if not m:
        await message.answer("Неверный формат. Введите время в формате <b>ЧЧ:ММ</b>, например: <code>08:00</code>")
        return
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer("Недопустимое время. Часы: 0-23, минуты: 0-59")
        return

    data = await state.get_data()
    times: list[str] = data.get("times", [])
    time_str = f"{hour:02d}:{minute:02d}"
    if time_str not in times:
        times.append(time_str)
    await state.update_data(times=times)
    await message.answer(
        f"✅ Добавлено время: <b>{time_str}</b>\n"
        f"Всего времён: {len(times)}: {', '.join(times)}\n\n"
        "Добавьте ещё или отправьте /done"
    )


@router.message(AddSupplementStates.waiting_stock_count)
async def process_stock_count(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit() or int(text) < 0:
        await message.answer("Введите целое число (0 и более):")
        return
    await state.update_data(stock_count=int(text))
    await state.set_state(AddSupplementStates.waiting_reorder_threshold)
    await message.answer(
        "⚠️ При каком остатке напомнить о заказе?\n"
        "(по умолчанию 10 — отправьте /skip чтобы оставить)"
    )


@router.message(AddSupplementStates.waiting_reorder_threshold, Command("skip"))
async def process_threshold_skip(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(reorder_threshold=10)
    await _save_supplement(message, state, session)


@router.message(AddSupplementStates.waiting_reorder_threshold)
async def process_threshold(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = message.text.strip()
    if not text.isdigit() or int(text) < 0:
        await message.answer("Введите целое число (0 и более) или /skip:")
        return
    await state.update_data(reorder_threshold=int(text))
    await _save_supplement(message, state, session)


async def _save_supplement(message: Message, state: FSMContext, session: AsyncSession) -> None:
    from aiogram import Bot
    bot: Bot = message.bot

    data = await state.get_data()
    await state.clear()

    user_repo = UserRepo(session)
    sup_repo = SupplementRepo(session)
    sched_repo = ScheduleRepo(session)
    stock_repo = StockRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return

    sup = await sup_repo.create(
        user_id=user.id,
        name=data["name"],
        dose_per_intake=data["dose"],
    )

    await stock_repo.create(
        supplement_id=sup.id,
        user_id=user.id,
        current_count=data["stock_count"],
        reorder_threshold=data["reorder_threshold"],
    )

    times_str_list = []
    for time_str in data["times"]:
        h, m = map(int, time_str.split(":"))
        schedule = await sched_repo.create(
            supplement_id=sup.id,
            user_id=user.id,
            hour=h,
            minute=m,
        )
        job_id = add_reminder_job(
            bot=bot,
            user_db_id=user.id,
            supplement_id=sup.id,
            schedule_id=schedule.id,
            hour=h,
            minute=m,
            timezone=user.timezone,
        )
        await sched_repo.set_job_id(schedule.id, job_id)
        times_str_list.append(time_str)

    add_stock_check_job(bot=bot, user_db_id=user.id, timezone=user.timezone)

    times_formatted = ", ".join(times_str_list)
    await message.answer(
        f"✅ <b>{data['name']}</b> добавлен!\n\n"
        f"💊 Доза: {data['dose']} шт.\n"
        f"⏰ Напоминания: {times_formatted}\n"
        f"📦 Запас: {data['stock_count']} шт. (алерт при {data['reorder_threshold']} шт.)\n\n"
        "Я буду напоминать вам каждый день!",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("supplements"))
@router.message(F.text == "💊 Мои БАД")
async def cmd_supplements(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepo(session)
    sup_repo = SupplementRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return

    supplements = await sup_repo.get_active_by_user(user.id)
    if not supplements:
        await message.answer(
            "У вас нет добавленных БАД.\n\nДобавьте через /add_supplement",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["💊 <b>Ваши БАД:</b>\n"]
    for sup in supplements:
        schedules = sup.schedules
        times = ", ".join(f"{s.hour:02d}:{s.minute:02d}" for s in schedules if s.is_active)
        stock_count = sup.stock.current_count if sup.stock else "—"
        lines.append(f"• <b>{sup.name}</b> — {sup.dose_per_intake} шт. | Остаток: {stock_count} | ⏰ {times}")

    await message.answer(
        "\n".join(lines) + "\n\nНажмите на БАД чтобы удалить его:",
        reply_markup=supplements_list_keyboard(supplements),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("del_supplement:"))
async def handle_delete_supplement(callback: CallbackQuery) -> None:
    supplement_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Вы уверены, что хотите удалить этот БАД?\nВсе напоминания будут отключены.",
        reply_markup=confirm_delete_keyboard(supplement_id),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_del:"))
async def handle_confirm_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    supplement_id = int(callback.data.split(":")[1])
    sup_repo = SupplementRepo(session)
    sched_repo = ScheduleRepo(session)

    user_repo = UserRepo(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    await sched_repo.deactivate_by_supplement(supplement_id)
    await sup_repo.deactivate(supplement_id)
    remove_jobs_for_supplement(user.id, supplement_id)

    await callback.message.edit_text("✅ БАД удалён. Напоминания отключены.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_del")
async def handle_cancel_delete(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Удаление отменено.")
    await callback.answer()


@router.message(Command("pause"))
async def cmd_pause(message: Message, session: AsyncSession) -> None:
    from bot.scheduler.manager import pause_user_jobs
    user_repo = UserRepo(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        return
    await user_repo.set_active(message.from_user.id, False)
    pause_user_jobs(user.id)
    await message.answer("⏸ Все напоминания приостановлены. Для возобновления: /resume")


@router.message(Command("resume"))
async def cmd_resume(message: Message, session: AsyncSession) -> None:
    from bot.scheduler.manager import resume_user_jobs
    user_repo = UserRepo(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        return
    await user_repo.set_active(message.from_user.id, True)
    resume_user_jobs(user.id)
    await message.answer("▶️ Напоминания возобновлены!")
