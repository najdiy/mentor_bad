import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from bot.config import settings
from bot.database.engine import init_db, AsyncSessionFactory
from bot.database.repositories import ScheduleRepo
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.scheduler.setup import get_scheduler
from bot.scheduler.manager import ensure_reminder_job, add_stock_check_job

from bot.handlers import start, supplements, intake, stock, stats, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="add_supplement", description="Добавить БАД"),
        BotCommand(command="supplements", description="Мои БАД"),
        BotCommand(command="my_schedule", description="Расписание на сегодня"),
        BotCommand(command="stock", description="Остатки"),
        BotCommand(command="update_stock", description="Обновить запас"),
        BotCommand(command="stats", description="Статистика приёмов"),
        BotCommand(command="timezone", description="Сменить часовой пояс"),
        BotCommand(command="pause", description="Приостановить напоминания"),
        BotCommand(command="resume", description="Возобновить напоминания"),
        BotCommand(command="help", description="Справка"),
    ]
    await bot.set_my_commands(commands)

    # Set Mini App button if WEBAPP_URL is set
    if settings.WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            )
            logger.info(f"MenuButtonWebApp set to {settings.WEBAPP_URL}")
        except Exception as e:
            logger.warning(f"Could not set MenuButtonWebApp: {e}")


async def restore_scheduler_jobs(bot: Bot) -> None:
    from sqlalchemy import select
    from bot.database.models import User

    async with AsyncSessionFactory() as session:
        async with session.begin():
            sched_repo = ScheduleRepo(session)
            schedules = await sched_repo.get_all_active()
            seen_users: set = set()

            for schedule in schedules:
                result = await session.execute(select(User).where(User.id == schedule.user_id))
                user = result.scalar_one_or_none()
                if not user or not user.is_active:
                    continue

                ensure_reminder_job(
                    bot=bot,
                    user_db_id=schedule.user_id,
                    supplement_id=schedule.supplement_id,
                    schedule_id=schedule.id,
                    hour=schedule.hour,
                    minute=schedule.minute,
                    timezone=user.timezone,
                )

                if schedule.user_id not in seen_users:
                    add_stock_check_job(bot=bot, user_db_id=schedule.user_id, timezone=user.timezone)
                    seen_users.add(schedule.user_id)

    logger.info("Scheduler jobs restored from DB")


async def main() -> None:
    await init_db()
    logger.info("Database initialized")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await setup_bot_commands(bot)

    dp = Dispatcher()
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))

    dp.include_router(start.router)
    dp.include_router(supplements.router)
    dp.include_router(intake.router)
    dp.include_router(stock.router)
    dp.include_router(stats.router)
    dp.include_router(admin.router)

    @dp.errors()
    async def error_handler(event, exception):
        logger.exception(f"Unhandled exception: {exception}")
        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(admin_id, f"⚠️ Ошибка:\n<code>{type(exception).__name__}: {exception}</code>")
            except Exception:
                pass

    scheduler = get_scheduler()
    await restore_scheduler_jobs(bot)
    scheduler.start()
    logger.info("Scheduler started")

    # FastAPI + uvicorn
    from api.app import create_app
    import uvicorn

    fastapi_app = create_app(bot=bot)
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    logger.info(f"Starting FastAPI on port {port}")
    logger.info("Bot started, polling...")

    try:
        await asyncio.gather(
            server.serve(),
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        )
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
