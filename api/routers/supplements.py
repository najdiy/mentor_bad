from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import SupplementOut, SupplementCreate
from bot.database.models import User
from bot.database.repositories import SupplementRepo, ScheduleRepo, StockRepo

router = APIRouter()


@router.get("/supplements", response_model=List[SupplementOut])
async def get_supplements(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = SupplementRepo(session)
    return await repo.get_active_by_user(current_user.id)


@router.post("/supplements", response_model=SupplementOut, status_code=201)
async def create_supplement(
    body: SupplementCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    sup_repo = SupplementRepo(session)
    sched_repo = ScheduleRepo(session)
    stock_repo = StockRepo(session)

    sup = await sup_repo.create(
        user_id=current_user.id,
        name=body.name,
        dose_per_intake=body.dose_per_intake,
    )
    await stock_repo.create(
        supplement_id=sup.id,
        user_id=current_user.id,
        current_count=body.stock_count,
        reorder_threshold=body.reorder_threshold,
    )

    bot = request.app.state.bot
    for time_str in body.times:
        h, m = map(int, time_str.split(":"))
        schedule = await sched_repo.create(
            supplement_id=sup.id,
            user_id=current_user.id,
            hour=h,
            minute=m,
        )
        if bot:
            from bot.scheduler.manager import add_reminder_job
            job_id = add_reminder_job(
                bot=bot,
                user_db_id=current_user.id,
                supplement_id=sup.id,
                schedule_id=schedule.id,
                hour=h,
                minute=m,
                timezone=current_user.timezone,
            )
            await sched_repo.set_job_id(schedule.id, job_id)

    if bot and body.times:
        from bot.scheduler.manager import add_stock_check_job
        add_stock_check_job(bot=bot, user_db_id=current_user.id, timezone=current_user.timezone)

    return await sup_repo.get_by_id(sup.id)


@router.delete("/supplements/{supplement_id}", status_code=204)
async def delete_supplement(
    supplement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    sup_repo = SupplementRepo(session)
    sched_repo = ScheduleRepo(session)

    sup = await sup_repo.get_by_id(supplement_id)
    if not sup or sup.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Supplement not found")

    await sched_repo.deactivate_by_supplement(supplement_id)
    await sup_repo.deactivate(supplement_id)

    from bot.scheduler.manager import remove_jobs_for_supplement
    remove_jobs_for_supplement(current_user.id, supplement_id)
