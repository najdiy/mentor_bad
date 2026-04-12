from __future__ import annotations
import logging
from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from bot.scheduler.setup import get_scheduler
from bot.scheduler.jobs import send_reminder, check_all_stock

logger = logging.getLogger(__name__)


def _reminder_job_id(user_db_id: int, supplement_id: int, schedule_id: int) -> str:
    return f"reminder:{user_db_id}:{supplement_id}:{schedule_id}"


def _stock_check_job_id(user_db_id: int) -> str:
    return f"stock_check:{user_db_id}"


def _snooze_job_id(user_db_id: int, snooze_id: int) -> str:
    return f"snooze:{user_db_id}:{snooze_id}"


def add_reminder_job(bot, user_db_id: int, supplement_id: int, schedule_id: int,
                     hour: int, minute: int, timezone: str) -> str:
    scheduler = get_scheduler()
    job_id = _reminder_job_id(user_db_id, supplement_id, schedule_id)
    scheduler.add_job(
        send_reminder,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id=job_id,
        replace_existing=True,
        kwargs={"bot": bot, "user_db_id": user_db_id, "supplement_id": supplement_id, "schedule_id": schedule_id},
    )
    logger.info(f"Added reminder job {job_id} at {hour:02d}:{minute:02d} {timezone}")
    return job_id


def remove_reminder_job(user_db_id: int, supplement_id: int, schedule_id: int) -> None:
    scheduler = get_scheduler()
    job_id = _reminder_job_id(user_db_id, supplement_id, schedule_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")


def remove_jobs_for_supplement(user_db_id: int, supplement_id: int) -> None:
    scheduler = get_scheduler()
    prefix = f"reminder:{user_db_id}:{supplement_id}:"
    for job in scheduler.get_jobs():
        if job.id.startswith(prefix):
            scheduler.remove_job(job.id)
            logger.info(f"Removed job {job.id}")


def pause_user_jobs(user_db_id: int) -> None:
    scheduler = get_scheduler()
    prefix = f"reminder:{user_db_id}:"
    for job in scheduler.get_jobs():
        if job.id.startswith(prefix):
            job.pause()


def resume_user_jobs(user_db_id: int) -> None:
    scheduler = get_scheduler()
    prefix = f"reminder:{user_db_id}:"
    for job in scheduler.get_jobs():
        if job.id.startswith(prefix):
            job.resume()


def add_snooze_job(bot, user_db_id: int, supplement_id: int, schedule_id: int,
                   log_id: int, remind_at: datetime, snooze_id: int) -> str:
    scheduler = get_scheduler()
    job_id = _snooze_job_id(user_db_id, snooze_id)

    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=remind_at),
        id=job_id,
        replace_existing=True,
        kwargs={"bot": bot, "user_db_id": user_db_id, "supplement_id": supplement_id, "schedule_id": schedule_id},
    )
    logger.info(f"Added snooze job {job_id} at {remind_at}")
    return job_id


def add_stock_check_job(bot, user_db_id: int, timezone: str) -> str:
    scheduler = get_scheduler()
    job_id = _stock_check_job_id(user_db_id)
    scheduler.add_job(
        check_all_stock,
        trigger=CronTrigger(hour=9, minute=0, timezone=timezone),
        id=job_id,
        replace_existing=True,
        kwargs={"bot": bot, "user_db_id": user_db_id},
    )
    logger.info(f"Added stock check job {job_id} at 09:00 {timezone}")
    return job_id


def ensure_reminder_job(bot, user_db_id: int, supplement_id: int, schedule_id: int,
                         hour: int, minute: int, timezone: str) -> str:
    scheduler = get_scheduler()
    job_id = _reminder_job_id(user_db_id, supplement_id, schedule_id)
    if not scheduler.get_job(job_id):
        return add_reminder_job(bot, user_db_id, supplement_id, schedule_id, hour, minute, timezone)
    return job_id
