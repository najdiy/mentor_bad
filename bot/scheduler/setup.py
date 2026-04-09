from __future__ import annotations
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot.config import settings

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{settings.SCHEDULER_DB}")
        }
        _scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")
    return _scheduler
