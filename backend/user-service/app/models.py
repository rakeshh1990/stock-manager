from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbols = Column(String, default="")  # comma-separated list for starter

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbols = Column(String, default="")
    __table_args__ = (UniqueConstraint('user_id', name='uq_watchlist_user'),)
