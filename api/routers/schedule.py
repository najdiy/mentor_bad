from typing import List

import pytz
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import ScheduleItem
from bot.database.models import User
from bot.database.repositories import IntakeLogRepo, SupplementRepo

router = APIRouter()


@router.get("/schedule/today", response_model=List[ScheduleItem])
async def get_today_schedule(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    log_repo = IntakeLogRepo(session)
    sup_repo = SupplementRepo(session)

    logs = await log_repo.get_today_by_user(current_user.id, current_user.timezone)
    supplements = await sup_repo.get_active_by_user(current_user.id)
    sup_map = {s.id: s for s in supplements}

    tz = pytz.timezone(current_user.timezone)
    result = []
    for log in logs:
        sup = sup_map.get(log.supplement_id)
        # Convert UTC scheduled_at to user's local time for display
        utc_time = pytz.utc.localize(log.scheduled_at)
        local_time = utc_time.astimezone(tz)
        result.append(ScheduleItem(
            log_id=log.id,
            supplement_id=log.supplement_id,
            supplement_name=sup.name if sup else f"БАД #{log.supplement_id}",
            scheduled_time=local_time.strftime("%H:%M"),
            status=log.status,
            dose=log.dose_taken,
        ))
    return result
