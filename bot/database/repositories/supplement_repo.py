from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from bot.database.models import Supplement


class SupplementRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, name: str, dose_per_intake: int = 1, description: Optional[str] = None) -> Supplement:
        supplement = Supplement(user_id=user_id, name=name, dose_per_intake=dose_per_intake, description=description)
        self.session.add(supplement)
        await self.session.flush()
        await self.session.refresh(supplement)
        return supplement

    async def get_by_id(self, supplement_id: int) -> Optional[Supplement]:
        result = await self.session.execute(
            select(Supplement)
            .options(selectinload(Supplement.schedules), selectinload(Supplement.stock))
            .where(Supplement.id == supplement_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: int) -> List[Supplement]:
        result = await self.session.execute(
            select(Supplement)
            .options(selectinload(Supplement.schedules), selectinload(Supplement.stock))
            .where(Supplement.user_id == user_id, Supplement.is_active == True)
            .order_by(Supplement.created_at)
        )
        return list(result.scalars().all())

    async def deactivate(self, supplement_id: int) -> None:
        await self.session.execute(
            update(Supplement).where(Supplement.id == supplement_id).values(is_active=False)
        )
