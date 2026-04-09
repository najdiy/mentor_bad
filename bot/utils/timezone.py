import pytz
from datetime import datetime

COMMON_TIMEZONES = [
    ("🇷🇺 Москва (UTC+3)", "Europe/Moscow"),
    ("🇷🇺 Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
    ("🇷🇺 Новосибирск (UTC+7)", "Asia/Novosibirsk"),
    ("🇷🇺 Владивосток (UTC+10)", "Asia/Vladivostok"),
    ("🇰🇿 Алматы (UTC+5)", "Asia/Almaty"),
    ("🇺🇿 Ташкент (UTC+5)", "Asia/Tashkent"),
    ("🇺🇦 Киев (UTC+2/3)", "Europe/Kiev"),
    ("🇧🇾 Минск (UTC+3)", "Europe/Minsk"),
    ("🇦🇿 Баку (UTC+4)", "Asia/Baku"),
    ("🇬🇧 Лондон (UTC+0/1)", "Europe/London"),
]

TIMEZONE_LABELS = {tz: label for label, tz in COMMON_TIMEZONES}


def now_in_tz(tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)


def is_valid_timezone(tz_name: str) -> bool:
    try:
        pytz.timezone(tz_name)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False
