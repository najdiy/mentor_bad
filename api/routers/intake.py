from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import IntakeAction
from bot.database.models import User
from bot.database.repositories import IntakeLogRepo
from bot.scheduler.jobs import send_low_stock_alert
from bot.services.intake_service import process_taken, process_skip, process_snooze

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

    log = await log_repo.get_by_id(log_id)
    if not log or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Log not found")
    if log.status in ("taken", "skipped"):
        raise HTTPException(status_code=409, detail="Already actioned")

    if body.action == "taken":
        result = await process_taken(session, log)
        if result.stock_low:
            bot = request.app.state.bot
            if bot:
                await send_low_stock_alert(
                    bot, current_user.telegram_id,
                    result.supplement_name, result.supplement_id, result.stock_count,
                )
        return {"status": "taken"}

    elif body.action == "skip":
        await process_skip(session, log)
        return {"status": "skipped"}

    elif body.action == "snooze":
        minutes = body.snooze_minutes or 30
        result = await process_snooze(session, log, minutes)

        bot = request.app.state.bot
        if not bot:
            return {"status": "snoozed", "remind_at": result.remind_at.isoformat()}

        from bot.scheduler.manager import add_snooze_job
        job_id = add_snooze_job(
            bot=bot,
            user_db_id=current_user.id,
            supplement_id=log.supplement_id,
            schedule_id=log.schedule_id,
            log_id=log.id,
            remind_at=result.remind_at,
            snooze_id=result.snooze_id,
        )
        from sqlalchemy import update
        from bot.database.models import SnoozeQueue
        await session.execute(
            update(SnoozeQueue).where(SnoozeQueue.id == result.snooze_id).values(job_id=job_id)
        )
        return {"status": "snoozed", "remind_at": result.remind_at.isoformat()}
