from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import StatsItem
from bot.database.models import User
from bot.database.repositories import IntakeLogRepo, SupplementRepo

router = APIRouter()


@router.get("/stats", response_model=List[StatsItem])
async def get_stats(
    period: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    log_repo = IntakeLogRepo(session)
    sup_repo = SupplementRepo(session)

    rows = await log_repo.get_stats_for_period(current_user.id, period, current_user.timezone)
    supplements = await sup_repo.get_active_by_user(current_user.id)
    sup_map = {s.id: s for s in supplements}

    result = []
    for row in rows:
        sup = sup_map.get(row["supplement_id"])
        if not sup:
            continue
        taken = row.get("taken", 0)
        skipped = row.get("skipped", 0)
        total = taken + skipped
        percent = round((taken / total * 100), 1) if total > 0 else 0.0
        result.append(StatsItem(
            supplement_id=row["supplement_id"],
            supplement_name=sup.name,
            taken=taken,
            skipped=skipped,
            total=total,
            percent=percent,
        ))
    return result
