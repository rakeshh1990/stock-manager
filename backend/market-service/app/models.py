from datetime import date, datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Date,
    DateTime, Boolean, UniqueConstraint, Index
)
from .database import Base


class PriceHistory(Base):
    """
    Daily OHLCV for every NSE-listed stock.
    Populated by the Bhavcopy ingestion job after market close.
    This is the single source of truth for all price data in the system —
    scanner, analyzer, and alert engine all read from here instead of
    making external API calls.
    """
    __tablename__ = "price_history"

    id         = Column(Integer, primary_key=True)
    symbol     = Column(String(20),  nullable=False)
    trade_date = Column(Date,        nullable=False)
    open       = Column(Float,       nullable=True)
    high       = Column(Float,       nullable=True)
    low        = Column(Float,       nullable=True)
    close      = Column(Float,       nullable=False)
    volume     = Column(Float,       nullable=True)
    series     = Column(String(10),  nullable=True)   # EQ, BE, SM etc.
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # One OHLCV row per symbol per trading day
        UniqueConstraint("symbol", "trade_date", name="uq_price_history_symbol_date"),
        Index("ix_price_history_symbol", "symbol"),
        Index("ix_price_history_trade_date", "trade_date"),
        Index("ix_price_history_symbol_date", "symbol", "trade_date"),
    )


class BhavCopyRun(Base):
    """
    Audit log of every Bhavcopy ingestion run.
    Used to detect missed days and to avoid double-ingestion.
    """
    __tablename__ = "bhavcopy_runs"

    id           = Column(Integer, primary_key=True)
    trade_date   = Column(Date,    nullable=False, unique=True)
    status       = Column(String(20), nullable=False)  # success | failed | partial
    rows_inserted= Column(Integer, nullable=True)
    error        = Column(String(500), nullable=True)
    ran_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))