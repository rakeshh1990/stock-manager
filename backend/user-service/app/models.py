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