"""Portfolio models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    is_paper_trading: Mapped[bool] = mapped_column(Boolean, default=False)
    
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    invested_capital: Mapped[float] = mapped_column(Float, default=0.0)
    cash_balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="INR")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="portfolios")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[str] = mapped_column(String(100), ForeignKey("instruments.id"), nullable=False, index=True)
    
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    average_buy_price: Mapped[float] = mapped_column(Float, default=0.0)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    portfolio = relationship("Portfolio", back_populates="positions")

    __table_args__ = (
        Index('ix_portfolio_pos_port_inst', 'portfolio_id', 'instrument_id', unique=True),
    )
