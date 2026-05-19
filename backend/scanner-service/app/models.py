from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from .database import Base


class ScanResult(Base):
    """
    Persisted result of one symbol from one scan run.
    scan_run_id groups all results from a single user-triggered scan.
    """
    __tablename__ = "scan_results"

    id             = Column(Integer, primary_key=True, index=True)
    scan_run_id    = Column(String(36), nullable=False, index=True)
    user_id        = Column(Integer, nullable=False, index=True)
    symbol         = Column(String(20), nullable=False)
    score          = Column(Integer, nullable=False)
    recommendation = Column(String(20), nullable=False)
    latest_close   = Column(Float, nullable=True)
    rsi            = Column(Float, nullable=True)
    momentum_5d    = Column(Float, nullable=True)
    ma_trend       = Column(String(10), nullable=True)
    macd_trend     = Column(String(10), nullable=True)
    volume_spike   = Column(Boolean, nullable=True)
    breakout       = Column(Boolean, nullable=True)
    in_watchlist   = Column(Boolean, default=False)
    error          = Column(Text, nullable=True)
    scanned_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))