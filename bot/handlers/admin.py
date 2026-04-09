import asyncio
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepo
from bot.filters.admin import IsAdmin
from bot.states.fsm import BroadcastStates

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"), IsAdmin())
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "/admin_stats — статистика пользователей\n"
        "/broadcast — рассылка всем пользователям"
    )


@router.message(Command("admin_stats"), IsAdmin())
async def cmd_admin_stats(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepo(session)
    total = await user_repo.count_active()
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Активных пользователей: <b>{total}</b>"
    )


@router.message(Command("broadcast"), IsAdmin())
async def cmd_broadcast_start(message: Message, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_message)
    await message.answer(
        "📢 Введите сообщение для рассылки всем пользователям.\n"
        "Отправьте /cancel чтобы отменить."
    )


@router.message(BroadcastStates.waiting_message, Command("cancel"))
async def cmd_broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Рассылка отменена.")


@router.message(BroadcastStates.waiting_message, IsAdmin())
async def cmd_broadcast_send(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    text = message.text

    user_repo = UserRepo(session)
    users = await user_repo.get_all_active()

    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(chat_id=user.telegram_id, text=text)
            sent += 1
            await asyncio.sleep(0.05)  # ~20 msg/sec, safely under 30/sec limit
        except Exception as e:
            logger.warning(f"Broadcast failed for {user.telegram_id}: {e}")
            failed += 1

    await message.answer(f"✅ Рассылка завершена.\nОтправлено: {sent} | Ошибок: {failed}")
