from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import StockOut, StockUpdate
from bot.database.models import User
from bot.database.repositories import StockRepo, SupplementRepo

router = APIRouter()


@router.get("/stock", response_model=List[StockOut])
async def get_stock(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)

    supplements = await sup_repo.get_active_by_user(current_user.id)
    sup_map = {s.id: s for s in supplements}
    stocks = await stock_repo.get_by_user(current_user.id)

    result = []
    for stock in stocks:
        sup = sup_map.get(stock.supplement_id)
        if not sup:
            continue
        result.append(StockOut(
            supplement_id=stock.supplement_id,
            supplement_name=sup.name,
            current_count=stock.current_count,
            reorder_threshold=stock.reorder_threshold,
            is_low=stock.current_count <= stock.reorder_threshold,
        ))
    return result


@router.patch("/stock/{supplement_id}", response_model=StockOut)
async def update_stock(
    supplement_id: int,
    body: StockUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stock_repo = StockRepo(session)
    sup_repo = SupplementRepo(session)

    sup = await sup_repo.get_by_id(supplement_id)
    if not sup or sup.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Supplement not found")

    await stock_repo.update_count(supplement_id, body.current_count)
    stock = await stock_repo.get_by_supplement(supplement_id)

    return StockOut(
        supplement_id=supplement_id,
        supplement_name=sup.name,
        current_count=stock.current_count,
        reorder_threshold=stock.reorder_threshold,
        is_low=stock.current_count <= stock.reorder_threshold,
    )
