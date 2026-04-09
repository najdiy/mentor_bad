from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import AsyncSessionFactory
from bot.database.models import User
from bot.database.repositories import UserRepo
from api.auth import validate_init_data, validate_init_data_dev
from bot.config import settings


async def get_session():
    async with AsyncSessionFactory() as session:
        async with session.begin():
            yield session


async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="X-Telegram-Init-Data header required")

    # In dev mode (no SECRET_KEY), skip HMAC check
    if not settings.SECRET_KEY:
        tg_user = validate_init_data_dev(x_telegram_init_data)
    else:
        tg_user = validate_init_data(x_telegram_init_data)

    repo = UserRepo(session)
    user, _ = await repo.upsert(
        telegram_id=tg_user["id"],
        full_name=tg_user.get("first_name", "") + " " + tg_user.get("last_name", ""),
        username=tg_user.get("username"),
    )
    return user
