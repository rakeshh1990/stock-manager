from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Portfolio, Watchlist
from .schemas import PortfolioIn, PortfolioOut

app = FastAPI(title="User Service")

@app.get("/health")
def health():
    return {"status": "ok", "service":"user-service"}

@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    p = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not p:
        return {"user_id": user_id, "symbols": []}
    syms = [s for s in (p.symbols or "").split(",") if s]
    return {"id": p.id, "user_id": p.user_id, "symbols": syms}

@app.post("/portfolio")
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
