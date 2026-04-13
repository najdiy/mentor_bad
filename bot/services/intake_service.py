"""Shared intake business logic for bot handlers and API routers."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import IntakeLog, SnoozeQueue
from bot.database.repositories import IntakeLogRepo, StockRepo, SupplementRepo


@dataclass
class IntakeResult:
    status: str
    stock_low: bool = False
    supplement_name: Optional[str] = None
    supplement_id: Optional[int] = None
    stock_count: Optional[int] = None
    remind_at: Optional[datetime] = None
    snooze_id: Optional[int] = None


async def process_taken(session: AsyncSession, log: IntakeLog) -> IntakeResult:
    log_repo = IntakeLogRepo(session)
    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)

    await log_repo.update_status(log.id, "taken")
    stock = await stock_repo.decrement(log.supplement_id, log.dose_taken)

    result = IntakeResult(status="taken")
    if stock and stock.current_count <= stock.reorder_threshold:
        sup = await sup_repo.get_by_id(log.supplement_id)
        if sup:
            result.stock_low = True
            result.supplement_name = sup.name
            result.supplement_id = sup.id
            result.stock_count = stock.current_count
    return result


async def process_skip(session: AsyncSession, log: IntakeLog) -> IntakeResult:
    log_repo = IntakeLogRepo(session)
    await log_repo.update_status(log.id, "skipped")
    return IntakeResult(status="skipped")


async def process_snooze(session: AsyncSession, log: IntakeLog, minutes: int) -> IntakeResult:
    remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
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

    return IntakeResult(
        status="snoozed",
        remind_at=remind_at,
        snooze_id=snooze.id,
    )
