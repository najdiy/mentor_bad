import hashlib
import hmac
import json
import time
from urllib.parse import unquote, parse_qsl

from fastapi import HTTPException, Header
from bot.config import settings


def validate_init_data(init_data: str) -> dict:
    """Validate Telegram WebApp initData via HMAC-SHA256."""
    try:
        decoded = unquote(init_data)
        params = dict(parse_qsl(decoded, keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData format")

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    # Build check string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    # check_hash = HMAC-SHA256(secret_key, data_check_string)
    check_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(check_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    # Check auth_date freshness (24 hours)
    auth_date = int(params.get("auth_date", 0))
    if abs(time.time() - auth_date) > 86400:
        raise HTTPException(status_code=401, detail="initData expired")

    # Parse user JSON
    user_json = params.get("user")
    if not user_json:
        raise HTTPException(status_code=401, detail="No user in initData")

    try:
        user = json.loads(user_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid user JSON")

    return user


def validate_init_data_dev(init_data: str) -> dict:
    """Dev mode: skip HMAC check, just parse user from initData."""
    try:
        decoded = unquote(init_data)
        params = dict(parse_qsl(decoded, keep_blank_values=True))
        user = json.loads(params.get("user", "{}"))
        if not user.get("id"):
            raise ValueError
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData")
