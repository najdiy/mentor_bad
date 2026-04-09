from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_current_user
from api.schemas import UserOut, UserUpdate
from bot.database.models import User
from bot.database.repositories import UserRepo
from bot.utils.timezone import is_valid_timezone

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepo(session)

    if body.timezone is not None:
        if not is_valid_timezone(body.timezone):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid timezone")
        await repo.update_timezone(current_user.telegram_id, body.timezone)
        current_user.timezone = body.timezone

    if body.is_active is not None:
        await repo.set_active(current_user.telegram_id, body.is_active)
        current_user.is_active = body.is_active

    return current_user
