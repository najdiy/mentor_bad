from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, field_validator
import re


class ScheduleItem(BaseModel):
    log_id: int
    supplement_id: int
    supplement_name: str
    scheduled_time: str   # "08:00"
    status: str
    dose: int

    class Config:
        from_attributes = True


class SupplementSchedule(BaseModel):
    id: int
    hour: int
    minute: int

    class Config:
        from_attributes = True


class StockInfo(BaseModel):
    current_count: int
    reorder_threshold: int

    class Config:
        from_attributes = True


class SupplementOut(BaseModel):
    id: int
    name: str
    dose_per_intake: int
    schedules: List[SupplementSchedule]
    stock: Optional[StockInfo]

    class Config:
        from_attributes = True


class SupplementCreate(BaseModel):
    name: str
    dose_per_intake: int = 1
    times: List[str]
    stock_count: int = 0
    reorder_threshold: int = 10

    @field_validator("times")
    @classmethod
    def validate_times(cls, v):
        pattern = re.compile(r"^\d{1,2}:\d{2}$")
        for t in v:
            if not pattern.match(t):
                raise ValueError(f"Invalid time format: {t}. Use HH:MM")
            h, m = map(int, t.split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError(f"Invalid time value: {t}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name too short")
        return v.strip()


class IntakeAction(BaseModel):
    action: Literal["taken", "skip", "snooze"]
    snooze_minutes: Optional[int] = None


class StockOut(BaseModel):
    supplement_id: int
    supplement_name: str
    current_count: int
    reorder_threshold: int
    is_low: bool

    class Config:
        from_attributes = True


class StockUpdate(BaseModel):
    current_count: int


class StatsItem(BaseModel):
    supplement_id: int
    supplement_name: str
    taken: int
    skipped: int
    total: int
    percent: float


class UserOut(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    timezone: str
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
