from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from bot.database.models import Schedule


class ScheduleRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, supplement_id: int, user_id: int, hour: int, minute: int, label: Optional[str] = None) -> Schedule:
        schedule = Schedule(supplement_id=supplement_id, user_id=user_id, hour=hour, minute=minute, label=label)
        self.session.add(schedule)
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def set_job_id(self, schedule_id: int, job_id: str) -> None:
        await self.session.execute(
            update(Schedule).where(Schedule.id == schedule_id).values(job_id=job_id)
        )

    async def get_active_by_user(self, user_id: int) -> List[Schedule]:
        result = await self.session.execute(
            select(Schedule)
            .options(selectinload(Schedule.supplement))
            .where(Schedule.user_id == user_id, Schedule.is_active == True)
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> List[Schedule]:
        result = await self.session.execute(
            select(Schedule)
            .options(selectinload(Schedule.supplement))
            .where(Schedule.is_active == True)
        )
        return list(result.scalars().all())

    async def deactivate_by_supplement(self, supplement_id: int) -> None:
        await self.session.execute(
            update(Schedule).where(Schedule.supplement_id == supplement_id).values(is_active=False)
        )

    async def deactivate_by_user(self, user_id: int) -> None:
        await self.session.execute(
            update(Schedule).where(Schedule.user_id == user_id).values(is_active=False)
        )
