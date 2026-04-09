from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Stock


class StockRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, supplement_id: int, user_id: int, current_count: int, reorder_threshold: int = 10) -> Stock:
        stock = Stock(supplement_id=supplement_id, user_id=user_id,
                      current_count=current_count, reorder_threshold=reorder_threshold)
        self.session.add(stock)
        await self.session.flush()
        await self.session.refresh(stock)
        return stock

    async def get_by_supplement(self, supplement_id: int) -> Optional[Stock]:
        result = await self.session.execute(
            select(Stock).where(Stock.supplement_id == supplement_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> List[Stock]:
        result = await self.session.execute(
            select(Stock).where(Stock.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_count(self, supplement_id: int, new_count: int) -> None:
        await self.session.execute(
            update(Stock).where(Stock.supplement_id == supplement_id).values(current_count=new_count)
        )

    async def decrement(self, supplement_id: int, amount: int) -> Optional[Stock]:
        stock = await self.get_by_supplement(supplement_id)
        if stock:
            new_count = max(0, stock.current_count - amount)
            await self.session.execute(
                update(Stock).where(Stock.supplement_id == supplement_id).values(current_count=new_count)
            )
            stock.current_count = new_count
        return stock

    async def get_low_stock_by_user(self, user_id: int) -> List[Stock]:
        result = await self.session.execute(
            select(Stock).where(
                Stock.user_id == user_id,
                Stock.current_count <= Stock.reorder_threshold,
            )
        )
        return list(result.scalars().all())
