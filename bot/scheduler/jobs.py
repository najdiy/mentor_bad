import logging
from datetime import datetime, timezone

from aiogram import Bot

from bot.database.engine import AsyncSessionFactory
from bot.database.repositories import UserRepo, SupplementRepo, IntakeLogRepo, StockRepo
from bot.keyboards.inline import reminder_keyboard, low_stock_keyboard

logger = logging.getLogger(__name__)


async def send_reminder(bot: Bot, user_db_id: int, supplement_id: int, schedule_id: int) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user_repo = UserRepo(session)
            sup_repo = SupplementRepo(session)
            log_repo = IntakeLogRepo(session)
            stock_repo = StockRepo(session)

            # Load supplement; skip if deleted
            sup = await sup_repo.get_by_id(supplement_id)
            if not sup or not sup.is_active:
                return

            # Load user by internal id
            from sqlalchemy import select
            from bot.database.models import User
            result = await session.execute(select(User).where(User.id == user_db_id))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                return

            stock = await stock_repo.get_by_supplement(supplement_id)
            stock_str = f"Остаток: {stock.current_count} шт." if stock else ""

            # Create intake log entry
            log = await log_repo.create(
                user_id=user_db_id,
                supplement_id=supplement_id,
                scheduled_at=datetime.now(timezone.utc),
                schedule_id=schedule_id,
                dose_taken=sup.dose_per_intake,
            )

            text = (
                f"⏰ <b>Время принять: {sup.name}</b>\n"
                f"💊 Доза: {sup.dose_per_intake} шт.\n"
                f"📦 {stock_str}"
            )
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=reminder_keyboard(log.id),
                )
            except Exception as e:
                logger.warning(f"Cannot send reminder to {user.telegram_id}: {e}")


async def send_low_stock_alert(bot: Bot, telegram_id: int, supplement_name: str, supplement_id: int, count: int) -> None:
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"⚠️ <b>Запас заканчивается!</b>\n\n"
                f"💊 {supplement_name}: осталось <b>{count} шт.</b>\n\n"
                "Не забудьте заказать пополнение на сайте Mentor Bads!"
            ),
            reply_markup=low_stock_keyboard(supplement_id),
        )
    except Exception as e:
        logger.warning(f"Cannot send low stock alert to {telegram_id}: {e}")


async def check_all_stock(bot: Bot, user_db_id: int) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            from sqlalchemy import select
            from bot.database.models import User, Supplement, Stock
            result = await session.execute(select(User).where(User.id == user_db_id))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                return

            stock_repo = StockRepo(session)
            low_stocks = await stock_repo.get_low_stock_by_user(user_db_id)
            for stock in low_stocks:
                sup_repo = SupplementRepo(session)
                sup = await sup_repo.get_by_id(stock.supplement_id)
                if sup and sup.is_active:
                    await send_low_stock_alert(bot, user.telegram_id, sup.name, sup.id, stock.current_count)
