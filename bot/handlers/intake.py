from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo, IntakeLogRepo
from bot.scheduler.manager import add_snooze_job
from bot.scheduler.jobs import send_low_stock_alert
from bot.services.intake_service import process_taken, process_skip, process_snooze

router = Router()


async def _get_log_or_error(callback: CallbackQuery, session: AsyncSession):
    log_id = int(callback.data.split(":")[1])
    log_repo = IntakeLogRepo(session)
    log = await log_repo.get_by_id(log_id)
    if not log:
        await callback.answer("Запись не найдена", show_alert=True)
        return None
    if log.status in ("taken", "skipped"):
        await callback.answer("Вы уже ответили на это напоминание", show_alert=True)
        return None
    return log


@router.callback_query(lambda c: c.data and c.data.startswith("taken:"))
async def handle_taken(callback: CallbackQuery, session: AsyncSession) -> None:
    log = await _get_log_or_error(callback, session)
    if not log:
        return

    result = await process_taken(session, log)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Принято!</b>"
    )
    await callback.answer("Отлично! Продолжайте в том же духе 💪")

    if result.stock_low:
        user_repo = UserRepo(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user:
            await send_low_stock_alert(
                callback.bot, user.telegram_id,
                result.supplement_name, result.supplement_id, result.stock_count,
            )


@router.callback_query(lambda c: c.data and c.data.startswith("skip:"))
async def handle_skip(callback: CallbackQuery, session: AsyncSession) -> None:
    log = await _get_log_or_error(callback, session)
    if not log:
        return

    await process_skip(session, log)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <i>Пропущено</i>"
    )
    await callback.answer("Понял, пропускаем.")


@router.callback_query(lambda c: c.data and (c.data.startswith("snooze_30:") or c.data.startswith("snooze_60:")))
async def handle_snooze(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    snooze_type = parts[0]
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

    result = await process_snooze(session, log, minutes)

    job_id = add_snooze_job(
        bot=callback.bot,
        user_db_id=user.id,
        supplement_id=log.supplement_id,
        schedule_id=log.schedule_id,
        log_id=log.id,
        remind_at=result.remind_at,
        snooze_id=result.snooze_id,
    )

    from sqlalchemy import update
    from bot.database.models import SnoozeQueue
    await session.execute(update(SnoozeQueue).where(SnoozeQueue.id == result.snooze_id).values(job_id=job_id))

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        callback.message.text + f"\n\n⏰ <i>Напомню через {minutes} мин.</i>"
    )
    await callback.answer(f"Напомню через {minutes} минут!")


@router.callback_query(lambda c: c.data and c.data.startswith("reorder_done:"))
async def handle_reorder_done(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "📦 Введите новое количество единиц в запасе:"
    )
    await callback.answer()
