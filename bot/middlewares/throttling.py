from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        self._cache: TTLCache = TTLCache(maxsize=10_000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            if user_id in self._cache:
                return None
            self._cache[user_id] = True
        return await handler(event, data)
