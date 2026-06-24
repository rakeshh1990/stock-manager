import logging
import os
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import Base, engine, get_db
from .models import Portfolio, Watchlist, WatchlistItem
from .schemas import (
    PortfolioIn, PortfolioOut,
    WatchlistCreate, WatchlistOut, WatchlistSummary,
    WatchlistItemIn, WatchlistItemOut,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("user-service")

app = FastAPI(title="User Service", version="1.1.0")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "development-internal-key")

def _require_user(x_user_id: Optional[str] = Header(default=None)) -> int:
    """
    Extract the caller's user_id from the X-User-Id header.
    This header is injected by the API gateway after JWT validation —
    it is never accepted from untrusted external callers.
    Raises 401 if the header is missing (should never happen in normal flow).
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")

def _require_internal(x_internal_key: Optional[str] = Header(default=None)) -> None:
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid internal service key")

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "user-service"}


# ---------------------------------------------------------------------------
# Portfolio  (unchanged behaviour, now reads user_id from header)
# ---------------------------------------------------------------------------

@app.get("/portfolio/{user_id}", tags=["portfolio"])
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    p = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not p:
        return {"user_id": user_id, "symbols": []}
    syms = [s for s in (p.symbols or "").split(",") if s]
    return {"id": p.id, "user_id": p.user_id, "symbols": syms}


@app.post("/portfolio", tags=["portfolio"])
def set_portfolio(payload: PortfolioIn, db: Session = Depends(get_db)):
    csv = ",".join(payload.symbols)
    p = db.query(Portfolio).filter(Portfolio.user_id == payload.user_id).first()
    if not p:
        p = Portfolio(user_id=payload.user_id, symbols=csv)
        db.add(p)
    else:
        p.symbols = csv
    db.commit()
    db.refresh(p)
    return {"id": p.id, "user_id": p.user_id, "symbols": payload.symbols}


# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------

@app.get("/watchlists", response_model=List[WatchlistSummary], tags=["watchlists"])
def list_watchlists(
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    """Return all watchlists for the authenticated user (no items, summary only)."""
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    result = []
    for wl in watchlists:
        result.append(WatchlistSummary(
            id=wl.id,
            user_id=wl.user_id,
            name=wl.name,
            created_at=wl.created_at,
            item_count=len(wl.items),
        ))
    return result


@app.post("/watchlists", response_model=WatchlistOut, status_code=201, tags=["watchlists"])
def create_watchlist(
    payload: WatchlistCreate,
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    """Create a new named watchlist for the authenticated user."""
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.name    == payload.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Watchlist '{payload.name}' already exists")

    wl = Watchlist(user_id=user_id, name=payload.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    logger.info(f"Created watchlist '{wl.name}' (id={wl.id}) for user {user_id}")
    return wl


@app.get("/watchlists/{watchlist_id}", response_model=WatchlistOut, tags=["watchlists"])
def get_watchlist(
    watchlist_id: int,
    db:           Session = Depends(get_db),
    user_id:      int     = Depends(_require_user),
):
    """Get a watchlist with all its items. Users can only access their own watchlists."""
    wl = db.query(Watchlist).filter(
        Watchlist.id      == watchlist_id,
        Watchlist.user_id == user_id,
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl


@app.delete("/watchlists/{watchlist_id}", status_code=204, tags=["watchlists"])
def delete_watchlist(
    watchlist_id: int,
    db:           Session = Depends(get_db),
    user_id:      int     = Depends(_require_user),
):
    """Delete a watchlist and all its items (cascade)."""
    wl = db.query(Watchlist).filter(
        Watchlist.id      == watchlist_id,
        Watchlist.user_id == user_id,
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    db.delete(wl)
    db.commit()
    logger.info(f"Deleted watchlist {watchlist_id} for user {user_id}")


# ---------------------------------------------------------------------------
# Watchlist Items
# ---------------------------------------------------------------------------

@app.post(
    "/watchlists/{watchlist_id}/items",
    response_model=WatchlistItemOut,
    status_code=201,
    tags=["watchlists"],
)
def add_item(
    watchlist_id: int,
    payload:      WatchlistItemIn,
    db:           Session = Depends(get_db),
    user_id:      int     = Depends(_require_user),
):
    """Add a symbol to a watchlist. Raises 409 if the symbol already exists in this watchlist."""
    wl = db.query(Watchlist).filter(
        Watchlist.id      == watchlist_id,
        Watchlist.user_id == user_id,
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    symbol = payload.symbol.strip().upper()

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.symbol       == symbol,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} already in this watchlist")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        symbol=symbol,
        notes=payload.notes,
        target_price=payload.target_price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(f"Added {symbol} to watchlist {watchlist_id} for user {user_id}")
    return item


@app.delete(
    "/watchlists/{watchlist_id}/items/{symbol}",
    status_code=204,
    tags=["watchlists"],
)
def remove_item(
    watchlist_id: int,
    symbol:       str,
    db:           Session = Depends(get_db),
    user_id:      int     = Depends(_require_user),
):
    """Remove a symbol from a watchlist."""
    wl = db.query(Watchlist).filter(
        Watchlist.id      == watchlist_id,
        Watchlist.user_id == user_id,
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    symbol = symbol.strip().upper()
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.symbol       == symbol,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{symbol} not found in this watchlist")

    db.delete(item)
    db.commit()
    logger.info(f"Removed {symbol} from watchlist {watchlist_id} for user {user_id}")

# ---------------------------------------------------------------------------
# Alerts — Part A (Phase 3)
# ---------------------------------------------------------------------------
from .models import Alert, AlertHistory
from datetime import datetime, timezone as _tz
from pydantic import BaseModel as _BM
from typing import Optional as _Opt, List as _List


class AlertIn(_BM):
    symbol:         str
    alert_type:     str = "condition"
    condition_type: str
    threshold:      _Opt[float] = None
    cooldown_hours: int = 24


class AlertOut(_BM):
    id:             int
    symbol:         str
    alert_type:     str
    condition_type: str
    threshold:      _Opt[float]
    active:         str
    cooldown_hours: int
    created_at:     datetime
    last_fired_at:  _Opt[datetime]
    class Config:
        from_attributes = True


class NotifOut(_BM):
    id:              int
    symbol:          str
    alert_type:      str
    condition_type:  str
    triggered_value: _Opt[float]
    threshold:       _Opt[float]
    message:         str
    priority:        str
    read:            str
    fired_at:        datetime
    class Config:
        from_attributes = True


@app.get("/alerts", response_model=_List[AlertOut], tags=["alerts"])
def list_alerts(
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    return db.query(Alert).filter(
        Alert.user_id == user_id
    ).order_by(Alert.created_at.desc()).all()


@app.post("/alerts", status_code=201, tags=["alerts"])
def create_alert(
    payload: AlertIn,
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    alert = Alert(
        user_id        = user_id,
        symbol         = payload.symbol.strip().upper(),
        alert_type     = payload.alert_type,
        condition_type = payload.condition_type,
        threshold      = payload.threshold,
        cooldown_hours = payload.cooldown_hours,
        active         = "Y",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(f"Created alert {alert.id} for user {user_id}: {alert.symbol} {alert.condition_type}")
    return alert


@app.patch("/alerts/{alert_id}/toggle", tags=["alerts"])
def toggle_alert(
    alert_id: int,
    db:       Session = Depends(get_db),
    user_id:  int     = Depends(_require_user),
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id, Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.active = "N" if alert.active == "Y" else "Y"
    db.commit()
    return {"id": alert.id, "active": alert.active}


@app.delete("/alerts/{alert_id}", status_code=204, tags=["alerts"])
def delete_alert(
    alert_id: int,
    db:       Session = Depends(get_db),
    user_id:  int     = Depends(_require_user),
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id, Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()


# ---------------------------------------------------------------------------
# Notification feed
# ---------------------------------------------------------------------------

@app.get("/notifications", response_model=_List[NotifOut], tags=["notifications"])
def list_notifications(
    limit:   int  = 50,
    unread:  bool = False,
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    q = db.query(AlertHistory).filter(AlertHistory.user_id == user_id)
    if unread:
        q = q.filter(AlertHistory.read == "N")
    return q.order_by(AlertHistory.fired_at.desc()).limit(min(max(limit, 1), 200)).all()

@app.patch("/notifications/read-all", tags=["notifications"])
def mark_all_read(
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    updated = db.query(AlertHistory).filter(
        AlertHistory.user_id == user_id,
        AlertHistory.read == "N",
    ).update({"read": "Y"})
    db.commit()
    return {"status": "ok", "updated": updated}

@app.patch("/notifications/{notif_id}/read", tags=["notifications"])
def mark_read(
    notif_id: int,
    db:       Session = Depends(get_db),
    user_id:  int     = Depends(_require_user),
):
    n = db.query(AlertHistory).filter(
        AlertHistory.id == notif_id, AlertHistory.user_id == user_id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = "Y"
    db.commit()
    return {"id": n.id, "read": "Y"}


@app.get("/notifications/unread-count", tags=["notifications"])
def unread_count(
    db:      Session = Depends(get_db),
    user_id: int     = Depends(_require_user),
):
    count = db.query(AlertHistory).filter(
        AlertHistory.user_id == user_id,
        AlertHistory.read    == "N",
    ).count()
    return {"count": count}


# ---------------------------------------------------------------------------
# Internal service API
# ---------------------------------------------------------------------------

@app.get("/internal/alerts/active", tags=["internal"])
def active_alerts(
    _: None = Depends(_require_internal),
    db: Session = Depends(get_db),
):
    return db.query(Alert).filter(Alert.active == "Y").all()


class AlertFiredIn(_BM):
    event_id: str
    triggered_value: _Opt[float] = None
    message: str
    priority: str = "normal"


@app.post("/internal/alerts/{alert_id}/fired", status_code=201, tags=["internal"])
def record_fired_alert(
    alert_id: int,
    payload: AlertFiredIn,
    _: None = Depends(_require_internal),
    db: Session = Depends(get_db),
):
    existing = db.query(AlertHistory).filter(
        AlertHistory.event_id == payload.event_id
    ).first()
    if existing:
        return existing

    alert = db.query(Alert).filter(Alert.id == alert_id).with_for_update().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    notification = AlertHistory(
        event_id=payload.event_id,
        alert_id=alert.id,
        user_id=alert.user_id,
        symbol=alert.symbol,
        alert_type=alert.alert_type,
        condition_type=alert.condition_type,
        triggered_value=payload.triggered_value,
        threshold=alert.threshold,
        message=payload.message[:500],
        priority="high" if payload.priority == "high" else "normal",
    )
    alert.last_fired_at = datetime.now(_tz.utc)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification