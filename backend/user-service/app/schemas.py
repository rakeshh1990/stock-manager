from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

class PortfolioIn(BaseModel):
    user_id: int
    symbols: List[str]

class PortfolioOut(BaseModel):
    id: int
    user_id: int
    symbols: List[str]


# ---------------------------------------------------------------------------
# Watchlist Item
# ---------------------------------------------------------------------------

class WatchlistItemIn(BaseModel):
    symbol:       str            = Field(..., min_length=1, max_length=20, example="INFY.NS")
    notes:        Optional[str]  = Field(None, max_length=500, example="Waiting for RSI dip below 40")
    target_price: Optional[Decimal] = Field(None, gt=0, example=1800.00)

class WatchlistItemOut(BaseModel):
    id:           int
    symbol:       str
    notes:        Optional[str]
    target_price: Optional[Decimal]
    added_at:     datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Midcap picks")

class WatchlistOut(BaseModel):
    id:         int
    user_id:    int
    name:       str
    created_at: datetime
    items:      List[WatchlistItemOut] = []

    class Config:
        from_attributes = True

class WatchlistSummary(BaseModel):
    """Returned in list view — no items, just metadata."""
    id:         int
    user_id:    int
    name:       str
    created_at: datetime
    item_count: int = 0

    class Config:
        from_attributes = True