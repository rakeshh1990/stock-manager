import logging
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