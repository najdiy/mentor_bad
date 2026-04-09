from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, ForeignKey, Integer, SmallInteger,
    String, Text, DateTime, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Moscow")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    supplements: Mapped[List["Supplement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    intake_logs: Mapped[List["IntakeLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Supplement(Base):
    __tablename__ = "supplements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dose_per_intake: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="supplements")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="supplement", cascade="all, delete-orphan")
    intake_logs: Mapped[List["IntakeLog"]] = relationship(back_populates="supplement", cascade="all, delete-orphan")
    stock: Mapped[Optional["Stock"]] = relationship(back_populates="supplement", uselist=False, cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplement_id: Mapped[int] = mapped_column(Integer, ForeignKey("supplements.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    minute: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    job_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    supplement: Mapped["Supplement"] = relationship(back_populates="schedules")
    intake_logs: Mapped[List["IntakeLog"]] = relationship(back_populates="schedule")


class IntakeLog(Base):
    __tablename__ = "intake_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    supplement_id: Mapped[int] = mapped_column(Integer, ForeignKey("supplements.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dose_taken: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    user: Mapped["User"] = relationship(back_populates="intake_logs")
    supplement: Mapped["Supplement"] = relationship(back_populates="intake_logs")
    schedule: Mapped[Optional["Schedule"]] = relationship(back_populates="intake_logs")


class Stock(Base):
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplement_id: Mapped[int] = mapped_column(Integer, ForeignKey("supplements.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    supplement: Mapped["Supplement"] = relationship(back_populates="stock")


class SnoozeQueue(Base):
    __tablename__ = "snooze_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    supplement_id: Mapped[int] = mapped_column(Integer, ForeignKey("supplements.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    intake_log_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("intake_logs.id", ondelete="SET NULL"), nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    original_scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
