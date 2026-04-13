from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import pytz
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from bot.database.models import IntakeLog


class IntakeLogRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, supplement_id: int, scheduled_at: datetime,
                     schedule_id: Optional[int] = None, dose_taken: int = 1) -> IntakeLog:
        log = IntakeLog(
            user_id=user_id,
            supplement_id=supplement_id,
            schedule_id=schedule_id,
            scheduled_at=scheduled_at,
            dose_taken=dose_taken,
            status="pending",
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: int) -> Optional[IntakeLog]:
        result = await self.session.execute(
            select(IntakeLog)
            .options(selectinload(IntakeLog.supplement))
            .where(IntakeLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, log_id: int, status: str) -> None:
        await self.session.execute(
            update(IntakeLog)
            .where(IntakeLog.id == log_id)
            .values(status=status, actioned_at=datetime.now(timezone.utc))
        )

    async def get_today_by_user(self, user_id: int, user_timezone: str = "UTC") -> List[IntakeLog]:
        tz = pytz.timezone(user_timezone)
        local_now = datetime.now(tz)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        # Convert local day boundaries to UTC for DB query
        today_start_utc = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        today_end_utc = local_end.astimezone(pytz.utc).replace(tzinfo=None)
        result = await self.session.execute(
            select(IntakeLog)
            .options(selectinload(IntakeLog.supplement))
            .where(
                IntakeLog.user_id == user_id,
                IntakeLog.scheduled_at >= today_start_utc,
                IntakeLog.scheduled_at < today_end_utc,
            )
            .order_by(IntakeLog.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_stats_for_period(self, user_id: int, days: int, user_timezone: str = "UTC") -> List[dict]:
        tz = pytz.timezone(user_timezone)
        local_now = datetime.now(tz)
        local_start = (local_now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        since = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        result = await self.session.execute(
            select(
                IntakeLog.supplement_id,
                IntakeLog.status,
                func.count().label("count"),
            )
            .where(IntakeLog.user_id == user_id, IntakeLog.scheduled_at >= since)
            .group_by(IntakeLog.supplement_id, IntakeLog.status)
        )
        rows = result.all()
        stats: dict = {}
        for row in rows:
            sid = row.supplement_id
            if sid not in stats:
                stats[sid] = {"supplement_id": sid, "taken": 0, "skipped": 0, "pending": 0, "total": 0}
            stats[sid][row.status] = row.count
            stats[sid]["total"] += row.count
        return list(stats.values())
