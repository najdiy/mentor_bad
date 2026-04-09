from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import IntakeAction
from bot.database.models import User, SnoozeQueue
from bot.database.repositories import IntakeLogRepo, StockRepo, SupplementRepo
from bot.scheduler.jobs import send_low_stock_alert

router = APIRouter()


@router.post("/intake/{log_id}/action", status_code=200)
async def intake_action(
    log_id: int,
    body: IntakeAction,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    log_repo = IntakeLogRepo(session)
    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)

    log = await log_repo.get_by_id(log_id)
    if not log or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Log not found")

    if log.status in ("taken", "skipped"):
        raise HTTPException(status_code=409, detail="Already actioned")

    if body.action == "taken":
        await log_repo.update_status(log_id, "taken")
        stock = await stock_repo.decrement(log.supplement_id, log.dose_taken)
        if stock and stock.current_count <= stock.reorder_threshold:
            sup = await sup_repo.get_by_id(log.supplement_id)
            if sup:
                bot = request.app.state.bot
                await send_low_stock_alert(bot, current_user.telegram_id, sup.name, sup.id, stock.current_count)
        return {"status": "taken"}

    elif body.action == "skip":
        await log_repo.update_status(log_id, "skipped")
        return {"status": "skipped"}

    elif body.action == "snooze":
        minutes = body.snooze_minutes or 30
        remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        snooze = SnoozeQueue(
            user_id=current_user.id,
            supplement_id=log.supplement_id,
            schedule_id=log.schedule_id,
            intake_log_id=log.id,
            remind_at=remind_at,
            original_scheduled_at=log.scheduled_at,
        )
        session.add(snooze)
        await session.flush()
        await session.refresh(snooze)

        bot = request.app.state.bot
        from bot.scheduler.manager import add_snooze_job
        job_id = add_snooze_job(
            bot=bot,
            user_db_id=current_user.id,
            supplement_id=log.supplement_id,
            schedule_id=log.schedule_id,
            log_id=log.id,
            remind_at=remind_at,
            snooze_id=snooze.id,
        )
        from sqlalchemy import update
        await session.execute(
            update(SnoozeQueue).where(SnoozeQueue.id == snooze.id).values(job_id=job_id)
        )
        return {"status": "snoozed", "remind_at": remind_at.isoformat()}
