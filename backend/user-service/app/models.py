from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric,
    ForeignKey, UniqueConstraint, func, Index
)
from sqlalchemy.orm import relationship
from .database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id      = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbols = Column(String, default="")   # comma-separated — will be replaced in a later phase


class Watchlist(Base):
    """
    A named watchlist owned by a user.
    One user can have many watchlists (e.g. 'Midcap picks', 'Swing trades').
    """
    __tablename__ = "watchlists"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False, index=True)
    name       = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_watchlist_user_name"),
        Index("ix_watchlists_user_id", "user_id"),
    )


class WatchlistItem(Base):
    """
    A single stock symbol entry inside a watchlist.
    Carries optional analyst notes and a target price for the alert engine.
    """
    __tablename__ = "watchlist_items"

    id           = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    symbol       = Column(String(20), nullable=False)
    notes        = Column(String(500), nullable=True)
    target_price = Column(Numeric(12, 2), nullable=True)
    added_at     = Column(DateTime(timezone=True), server_default=func.now())

    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_item_symbol"),
    )

class Alert(Base):
    """
    User-defined alert on a stock symbol.
    alert_type: 'condition' (user-created) | 'exit_watch' (auto for portfolio holdings)
    condition_type: RSI_BELOW | RSI_ABOVE | PRICE_BELOW | PRICE_ABOVE |
                    MOMENTUM_NEG | SCORE_DROP | EXIT_SIGNAL
    """
    __tablename__ = "alerts"

    id             = Column(Integer, primary_key=True)
    user_id        = Column(Integer, nullable=False, index=True)
    symbol         = Column(String(20), nullable=False)
    alert_type     = Column(String(20), nullable=False, default="condition")
    condition_type = Column(String(20), nullable=False)
    threshold      = Column(Numeric(12, 2), nullable=True)
    active         = Column(String(1), nullable=False, default="Y")  # Y | N
    cooldown_hours = Column(Integer, default=24)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    last_fired_at  = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
    )


class AlertHistory(Base):
    """Immutable record of every fired alert — drives the in-app notification feed."""
    __tablename__ = "alert_history"

    id              = Column(Integer, primary_key=True)
    event_id        = Column(String(36), nullable=True, unique=True, index=True)
    alert_id        = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    user_id         = Column(Integer, nullable=False, index=True)
    symbol          = Column(String(20), nullable=False)
    alert_type      = Column(String(20), nullable=False)
    condition_type  = Column(String(20), nullable=False)
    triggered_value = Column(Numeric(12, 4), nullable=True)
    threshold       = Column(Numeric(12, 2), nullable=True)
    message         = Column(String(500), nullable=False)
    priority        = Column(String(10), nullable=False, default="normal")  # normal | high
    read            = Column(String(1), nullable=False, default="N")
    fired_at        = Column(DateTime(timezone=True), server_default=func.now())