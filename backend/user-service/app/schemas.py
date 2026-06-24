from pydantic import BaseModel, Field
from typing import List, Literal, Optional
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


ConditionType = Literal[
    "RSI_BELOW", "RSI_ABOVE", "PRICE_BELOW", "PRICE_ABOVE",
    "MOMENTUM_NEG", "SCORE_DROP", "EXIT_SIGNAL",
]


class AlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, examples=["INFY"])
    alert_type: Literal["condition", "exit_watch"] = "condition"
    condition_type: ConditionType
    threshold: Optional[Decimal] = None
    cooldown_hours: int = Field(default=24, ge=0, le=720)


class AlertOut(BaseModel):
    id: int
    user_id: int
    symbol: str
    alert_type: str
    condition_type: str
    threshold: Optional[Decimal]
    active: str
    cooldown_hours: int
    created_at: datetime
    last_fired_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    alert_id: Optional[int]
    user_id: int
    symbol: str
    alert_type: str
    condition_type: str
    triggered_value: Optional[Decimal]
    threshold: Optional[Decimal]
    message: str
    priority: str
    read: str
    fired_at: datetime

    class Config:
        from_attributes = True


class AlertFiredIn(BaseModel):
    triggered_value: Optional[Decimal] = None
    message: str = Field(..., min_length=1, max_length=500)
    priority: Literal["normal", "high"] = "normal"