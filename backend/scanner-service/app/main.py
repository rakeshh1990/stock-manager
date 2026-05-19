import os
import json
import time
import random
import logging
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

import httpx
import yfinance as yf
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from .database import SessionLocal
from .models import ScanResult  # noqa — model defined in models.py, registered on Base
from .symbols import SCAN_SCOPES

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("scanner-service")




# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Scanner Service", version="1.0.0")

_executor = ThreadPoolExecutor(max_workers=5)

# User-service URL — scanner calls this API to get watchlist symbols.
# Scanner never touches user-service's database directly; the API is
# the contract. If user-service changes its schema, scanner is unaffected.
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8004")



# ---------------------------------------------------------------------------
# Auth helper — trusts X-User-Id injected by the gateway after JWT validation
# ---------------------------------------------------------------------------
def _require_user(x_user_id: Optional[str] = Header(default=None)) -> int:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")


# ---------------------------------------------------------------------------
# Core analysis — runs in thread pool
# ---------------------------------------------------------------------------
# Shared requests session with browser-like headers — constructed once per
# process so all threads reuse the same connection pool.
# Yahoo Finance returns empty JSON (line 1 col 1) when it detects bot traffic;
# these headers make requests look like a real browser.
import requests as _requests
_YF_SESSION = _requests.Session()
_YF_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
})


def _analyse_symbol(symbol: str) -> dict:
    """
    Fetch 6 months of daily OHLCV and compute technical indicators.
    Random sleep staggers requests; browser-like session headers prevent
    Yahoo Finance from returning empty responses to bot-like requests.
    """
    time.sleep(random.uniform(1.0, 3.0))
    try:
        ticker = yf.Ticker(symbol, session=_YF_SESSION)
        df = ticker.history(period="6mo", interval="1d", auto_adjust=True)

        if df is None or df.empty or len(df) < 30:
            time.sleep(4)
            ticker = yf.Ticker(symbol, session=_YF_SESSION)
            df = ticker.history(period="6mo", interval="1d", auto_adjust=True)
            if df is None or df.empty or len(df) < 30:
                return {"symbol": symbol, "error": "Insufficient data after retry"}

        close  = df["Close"].squeeze()
        volume = df["Volume"].squeeze()

        # RSI (14)
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi   = float((100 - 100 / (1 + rs)).iloc[-1])

        # MACD
        ema12       = close.ewm(span=12).mean()
        ema26       = close.ewm(span=26).mean()
        macd_line   = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_bull   = float(macd_line.iloc[-1]) > float(signal_line.iloc[-1])

        # Moving averages
        price   = float(close.iloc[-1])
        ma50    = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        ma_bull = ma50 is not None and price > ma50

        # 5-day momentum
        momentum = float(
            (price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100
        ) if len(close) >= 6 else 0.0

        # Volume spike
        avg_vol    = float(volume.rolling(20).mean().iloc[-1])
        recent_vol = float(volume.iloc[-1])
        vol_spike  = recent_vol > avg_vol * 1.5

        # 20-day breakout
        high_20  = float(close.rolling(20).max().iloc[-2]) if len(close) >= 21 else None
        breakout = high_20 is not None and price > high_20

        # Score
        score = 0
        if rsi < 30:      score += 3
        elif rsi < 50:    score += 1
        elif rsi > 70:    score -= 2
        if macd_bull:     score += 2
        if ma_bull:       score += 2
        if momentum > 2:  score += 1
        if momentum < -3: score -= 1
        if vol_spike:     score += 1
        if breakout:      score += 1

        if score >= 6:    rec = "STRONG BUY"
        elif score >= 3:  rec = "BUY"
        elif score >= 0:  rec = "HOLD"
        else:             rec = "SELL"

        return {
            "symbol":         symbol,
            "score":          score,
            "recommendation": rec,
            "latest_close":   round(price, 2),
            "rsi":            round(rsi, 2),
            "momentum_5d":    round(momentum, 2),
            "ma_trend":       "bull" if ma_bull else "bear",
            "macd_trend":     "bull" if macd_bull else "bear",
            "volume_spike":   vol_spike,
            "breakout":       breakout,
            "error":          None,
        }
    except Exception as e:
        logger.warning(f"Failed to analyse {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


# ---------------------------------------------------------------------------
# SSE scan stream
# ---------------------------------------------------------------------------
@app.get("/scan/stream")
async def scan_stream(
    scope:     str = Query("nifty50", enum=["nifty50", "nifty100"]),
    x_user_id: Optional[str] = Header(default=None),
):
    user_id = None
    if x_user_id:
        try:
            user_id = int(x_user_id)
        except ValueError:
            pass

    symbols = SCAN_SCOPES.get(scope, SCAN_SCOPES["nifty50"])

    # Fetch watchlist symbols via user-service API — not direct DB access.
    # Scanner owns scanner_db; user-service owns user_db.
    # Cross-service data access goes through the published API, not shared tables.
    watchlist_symbols: set = set()
    if user_id:
        try:
            async with httpx.AsyncClient(timeout=5) as http:
                r = await http.get(
                    f"{USER_SERVICE_URL}/watchlists",
                    headers={"X-User-Id": str(user_id)},
                )
            if r.status_code == 200:
                summaries = r.json()
                # Fetch each watchlist for its items
                symbol_set = set()
                async with httpx.AsyncClient(timeout=5) as http:
                    for wl in summaries:
                        wr = await http.get(
                            f"{USER_SERVICE_URL}/watchlists/{wl['id']}",
                            headers={"X-User-Id": str(user_id)},
                        )
                        if wr.status_code == 200:
                            for item in wr.json().get("items", []):
                                symbol_set.add(item["symbol"])
                watchlist_symbols = symbol_set
                logger.info(f"Fetched {len(watchlist_symbols)} watchlist symbols for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not fetch watchlist symbols from user-service: {e}")

    scan_run_id = str(uuid.uuid4())
    start_time  = time.time()

    async def event_generator():
        loop    = asyncio.get_event_loop()
        results = []
        bullish = 0

        futures = {
            loop.run_in_executor(_executor, _analyse_symbol, sym): sym
            for sym in symbols
        }

        for future in asyncio.as_completed(futures.keys()):
            result = await future
            result["in_watchlist"] = result["symbol"] in watchlist_symbols

            if result.get("error"):
                event = json.dumps({"type": "error", "data": {
                    "symbol":  result["symbol"],
                    "message": result["error"],
                }})
            else:
                if result["recommendation"] in ("STRONG BUY", "BUY"):
                    bullish += 1
                results.append(result)
                event = json.dumps({"type": "progress", "data": result})

            yield f"data: {event}\n\n"
            await asyncio.sleep(0)

        # Persist results
        if user_id and results:
            try:
                db = SessionLocal()
                for r in results:
                    db.add(ScanResult(
                        scan_run_id    = scan_run_id,
                        user_id        = user_id,
                        symbol         = r["symbol"],
                        score          = r.get("score", 0),
                        recommendation = r.get("recommendation", "HOLD"),
                        latest_close   = r.get("latest_close"),
                        rsi            = r.get("rsi"),
                        momentum_5d    = r.get("momentum_5d"),
                        ma_trend       = r.get("ma_trend"),
                        macd_trend     = r.get("macd_trend"),
                        volume_spike   = r.get("volume_spike"),
                        breakout       = r.get("breakout"),
                        in_watchlist   = r.get("in_watchlist", False),
                    ))
                db.commit()
                db.close()
                logger.info(f"Persisted {len(results)} scan results for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to persist scan results: {e}")

        duration   = round(time.time() - start_time, 1)
        done_event = json.dumps({"type": "done", "data": {
            "scan_run_id": scan_run_id,
            "total":       len(symbols),
            "completed":   len(results),
            "bullish":     bullish,
            "duration_s":  duration,
        }})
        yield f"data: {done_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Latest scan results
# ---------------------------------------------------------------------------
@app.get("/scan/results")
def get_latest_results(x_user_id: Optional[str] = Header(default=None)):
    user_id = _require_user(x_user_id)
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT scan_run_id FROM scan_results WHERE user_id = :uid ORDER BY scanned_at DESC LIMIT 1"),
            {"uid": user_id},
        ).fetchone()

        if not row:
            return {"results": [], "scan_run_id": None, "scanned_at": None}

        run_id = row[0]
        rows = db.execute(
            text(
                "SELECT symbol, score, recommendation, latest_close, rsi, "
                "momentum_5d, ma_trend, macd_trend, volume_spike, breakout, "
                "in_watchlist, scanned_at FROM scan_results "
                "WHERE scan_run_id = :run_id ORDER BY score DESC"
            ),
            {"run_id": run_id},
        ).fetchall()

        keys = [
            "symbol", "score", "recommendation", "latest_close", "rsi",
            "momentum_5d", "ma_trend", "macd_trend", "volume_spike",
            "breakout", "in_watchlist", "scanned_at",
        ]
        results = []
        for r in rows:
            d = dict(zip(keys, r))
            d["scanned_at"] = d["scanned_at"].isoformat() if d["scanned_at"] else None
            results.append(d)

        return {
            "scan_run_id": run_id,
            "scanned_at":  results[0]["scanned_at"] if results else None,
            "results":     results,
        }
    finally:
        db.close()


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "scanner-service"}