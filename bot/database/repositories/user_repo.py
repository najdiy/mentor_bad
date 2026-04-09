from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, full_name: str, username: Optional[str], timezone: str = "Europe/Moscow") -> User:
        user = User(telegram_id=telegram_id, full_name=full_name, username=username, timezone=timezone)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def upsert(self, telegram_id: int, full_name: str, username: Optional[str]) -> tuple:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.full_name = full_name
            user.username = username
            await self.session.flush()
            return user, False
        user = await self.create(telegram_id, full_name, username)
        return user, True

    async def update_timezone(self, telegram_id: int, timezone: str) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(timezone=timezone)
        )

    async def set_active(self, telegram_id: int, is_active: bool) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_active=is_active)
        )

    async def get_all_active(self) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())

    async def count_active(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_active == True)
        )
        return result.scalar_one()
