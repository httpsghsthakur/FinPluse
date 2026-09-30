"""Market data models."""
from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import String, Float, Boolean, DateTime, Date, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    trading_symbol: Mapped[str] = mapped_column(String(100), nullable=True)
    instrument_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(20), nullable=False) # EQ, IND, FNO
    sector: Mapped[str] = mapped_column(String(100), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    lot_size: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    instrument_id: Mapped[str] = mapped_column(String(100), ForeignKey("instruments.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    
    ltp: Mapped[float] = mapped_column(Float, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=True)
    high: Mapped[float] = mapped_column(Float, nullable=True)
    low: Mapped[float] = mapped_column(Float, nullable=True)
    close: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)
    
    change: Mapped[float] = mapped_column(Float, nullable=True)
    change_percent: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_market_snapshots_inst_time', 'instrument_id', 'timestamp'),
    )


class HistoricalCandle(Base):
    __tablename__ = "historical_candles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    instrument_id: Mapped[str] = mapped_column(String(100), ForeignKey("instruments.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    interval: Mapped[str] = mapped_column(String(20), nullable=False) # 1d, 1wk, 1mo, 1m, 5m, etc.
    
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_historical_candles_inst_time_int', 'instrument_id', 'timestamp', 'interval', unique=True),
    )
