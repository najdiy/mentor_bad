from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo, IntakeLogRepo, StockRepo, SupplementRepo
from bot.scheduler.manager import add_snooze_job
from bot.scheduler.jobs import send_low_stock_alert

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("taken:"))
async def handle_taken(callback: CallbackQuery, session: AsyncSession) -> None:
    log_id = int(callback.data.split(":")[1])
    log_repo = IntakeLogRepo(session)
    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)
    user_repo = UserRepo(session)

    log = await log_repo.get_by_id(log_id)
    if not log:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if log.status in ("taken", "skipped"):
        await callback.answer("Вы уже ответили на это напоминание", show_alert=True)
        return

    await log_repo.update_status(log_id, "taken")

    # Decrement stock
    stock = await stock_repo.decrement(log.supplement_id, log.dose_taken)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Принято!</b>"
    )
    await callback.answer("Отлично! Продолжайте в том же духе 💪")

    # Check low stock
    if stock and stock.current_count <= stock.reorder_threshold:
        sup = await sup_repo.get_by_id(log.supplement_id)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if sup and user:
            await send_low_stock_alert(callback.bot, user.telegram_id, sup.name, sup.id, stock.current_count)


@router.callback_query(lambda c: c.data and c.data.startswith("skip:"))
async def handle_skip(callback: CallbackQuery, session: AsyncSession) -> None:
    log_id = int(callback.data.split(":")[1])
    log_repo = IntakeLogRepo(session)

    log = await log_repo.get_by_id(log_id)
    if not log:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if log.status in ("taken", "skipped"):
        await callback.answer("Вы уже ответили на это напоминание", show_alert=True)
        return

    await log_repo.update_status(log_id, "skipped")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <i>Пропущено</i>"
    )
    await callback.answer("Понял, пропускаем.")


@router.callback_query(lambda c: c.data and (c.data.startswith("snooze_30:") or c.data.startswith("snooze_60:")))
async def handle_snooze(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    snooze_type = parts[0]  # snooze_30 or snooze_60
    log_id = int(parts[1])
    minutes = 30 if snooze_type == "snooze_30" else 60

    log_repo = IntakeLogRepo(session)
    user_repo = UserRepo(session)

    log = await log_repo.get_by_id(log_id)
    if not log:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if log.status in ("taken", "skipped"):
        await callback.answer("Вы уже ответили на это напоминание", show_alert=True)
        return

    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    # Save snooze to DB
    from bot.database.models import SnoozeQueue
    snooze = SnoozeQueue(
        user_id=log.user_id,
        supplement_id=log.supplement_id,
        schedule_id=log.schedule_id,
        intake_log_id=log.id,
        remind_at=remind_at,
        original_scheduled_at=log.scheduled_at,
    )
    session.add(snooze)
    await session.flush()
    await session.refresh(snooze)

    job_id = add_snooze_job(
        bot=callback.bot,
        user_db_id=user.id,
        supplement_id=log.supplement_id,
        schedule_id=log.schedule_id,
        log_id=log.id,
        remind_at=remind_at,
        snooze_id=snooze.id,
    )

    from sqlalchemy import update
    from bot.database.models import SnoozeQueue as SQ
    await session.execute(update(SQ).where(SQ.id == snooze.id).values(job_id=job_id))

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + f"\n\n⏰ <i>Напомню через {minutes} мин.</i>"
    )
    await callback.answer(f"Напомню через {minutes} минут!")


@router.callback_query(lambda c: c.data and c.data.startswith("reorder_done:"))
async def handle_reorder_done(callback: CallbackQuery, session: AsyncSession) -> None:
    supplement_id = int(callback.data.split(":")[1])
    from bot.states.fsm import UpdateStockStates
    from aiogram.fsm.context import FSMContext

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "📦 Введите новое количество единиц в запасе:"
    )
    # Store supplement_id in FSM via update_stock flow
    await callback.answer()
