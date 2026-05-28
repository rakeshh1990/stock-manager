import os
import json
import time
import logging
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional, List

import httpx
import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from .database import SessionLocal
from .models import ScanResult

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("scanner-service")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
USER_SERVICE_URL   = os.getenv("USER_SERVICE_URL",   "http://user-service:8004")
MARKET_SERVICE_URL = os.getenv("MARKET_SERVICE_URL", "http://market-service:8006")

# ---------------------------------------------------------------------------
# Symbol resolution — fetched from market-service, not hardcoded
# ---------------------------------------------------------------------------
_SYMBOL_CACHE: dict = {}
_SYMBOL_CACHE_TTL = 6 * 3600   # 6 hours — same as market-service


def _get_symbols(scope: str) -> list:
    """
    Fetch index constituents from market-service.
    Falls back to a minimal hardcoded list if market-service is unavailable.
    Results cached for 6 hours — index composition changes quarterly.
    """
    now = time.time()
    cached = _SYMBOL_CACHE.get(scope)
    if cached and (now - cached["fetched_at"]) < _SYMBOL_CACHE_TTL:
        return cached["symbols"]

    # Map scan scope to market-service index name
    index_map = {
        "nifty50":  "nifty50",
        "nifty100": "nifty100",
    }
    index = index_map.get(scope, "nifty50")

    try:
        r = httpx.get(
            f"{MARKET_SERVICE_URL}/constituents/{index}",
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            symbols = data.get("symbols", [])
            if symbols:
                _SYMBOL_CACHE[scope] = {"symbols": symbols, "fetched_at": now}
                logger.info(f"Fetched {len(symbols)} symbols for scope '{scope}' from market-service ({data.get('source')})")
                return symbols
    except Exception as e:
        logger.warning(f"Could not fetch symbols from market-service: {e}")

    # Fallback — return empty so scan fails gracefully rather than using stale data
    logger.error(f"Symbol fetch failed for scope '{scope}' — no scan will run")
    return []


app = FastAPI(title="Scanner Service", version="2.0.0")
_executor = ThreadPoolExecutor(max_workers=8)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def _require_user(x_user_id: Optional[str] = None) -> int:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")


# ---------------------------------------------------------------------------
# Core: fetch price data from market-service and compute indicators
# ---------------------------------------------------------------------------
def _fetch_price_data(symbol: str) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV from market-service (local DB — no external API calls).
    symbols.py now uses bare Bhavcopy symbols directly — no mapping needed.
    Returns a pandas DataFrame or None if no data available.
    """
    try:
        # symbols.py already uses bare NSE tickers matching Bhavcopy
        nse_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()
        r = httpx.get(
            f"{MARKET_SERVICE_URL}/history/{nse_symbol}",
            params={"days": 200},
            timeout=10,
        )
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            logger.warning(f"market-service returned {r.status_code} for {nse_symbol}")
            return None
        data = r.json()
        df = pd.DataFrame(data)
        df["trade_date"] = pd.to_datetime(df["date"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        return df
    except Exception as e:
        logger.warning(f"Failed to fetch price data for {symbol}: {e}")
        return None


def _compute_indicators(df: pd.DataFrame) -> dict:
    """Compute RSI, MACD, MA50, momentum, volume spike, breakout from OHLCV DataFrame."""
    close  = df["close"].astype(float)
    volume = df["volume"].astype(float) if "volume" in df.columns else None

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

    # MA50
    price   = float(close.iloc[-1])
    ma50    = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    ma_bull = ma50 is not None and price > ma50

    # 5-day momentum
    momentum = float(
        (price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100
    ) if len(close) >= 6 else 0.0

    # Volume spike
    vol_spike = False
    if volume is not None and len(volume) >= 20:
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


def _analyse_symbol(symbol: str) -> dict:
    """Full analysis for one symbol — fetch from market-service + compute indicators."""
    df = _fetch_price_data(symbol)
    if df is None or len(df) < 30:
        return {"symbol": symbol, "error": "Insufficient price data"}
    try:
        result = _compute_indicators(df)
        result["symbol"] = symbol
        return result
    except Exception as e:
        logger.warning(f"Indicator computation failed for {symbol}: {e}")
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

    symbols = _get_symbols(scope)

    # Fetch watchlist symbols via user-service API
    watchlist_symbols: set = set()
    if user_id:
        try:
            async with httpx.AsyncClient(timeout=5) as http:
                r = await http.get(
                    f"{USER_SERVICE_URL}/watchlists",
                    headers={"X-User-Id": str(user_id)},
                )
            if r.status_code == 200:
                symbol_set = set()
                async with httpx.AsyncClient(timeout=5) as http:
                    for wl in r.json():
                        wr = await http.get(
                            f"{USER_SERVICE_URL}/watchlists/{wl['id']}",
                            headers={"X-User-Id": str(user_id)},
                        )
                        if wr.status_code == 200:
                            for item in wr.json().get("items", []):
                                symbol_set.add(item["symbol"])
                watchlist_symbols = symbol_set
        except Exception as e:
            logger.warning(f"Could not fetch watchlist: {e}")

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
            # Match watchlist — strip .NS for comparison
            nse_sym = result["symbol"].replace(".NS", "")
            result["in_watchlist"] = (
                result["symbol"] in watchlist_symbols or
                nse_sym in watchlist_symbols
            )

            if result.get("error"):
                event = json.dumps({"type": "error", "data": {
                    "symbol": result["symbol"], "message": result["error"],
                }})
            else:
                if result["recommendation"] in ("STRONG BUY", "BUY"):
                    bullish += 1
                results.append(result)
                event = json.dumps({"type": "progress", "data": result})

            yield f"data: {event}\n\n"
            await asyncio.sleep(0)

        # Persist
        if user_id and results:
            try:
                db = SessionLocal()
                for r in results:
                    db.add(ScanResult(
                        scan_run_id=scan_run_id, user_id=user_id,
                        symbol=r["symbol"], score=r.get("score", 0),
                        recommendation=r.get("recommendation", "HOLD"),
                        latest_close=r.get("latest_close"), rsi=r.get("rsi"),
                        momentum_5d=r.get("momentum_5d"), ma_trend=r.get("ma_trend"),
                        macd_trend=r.get("macd_trend"), volume_spike=r.get("volume_spike"),
                        breakout=r.get("breakout"), in_watchlist=r.get("in_watchlist", False),
                    ))
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to persist results: {e}")

        done_event = json.dumps({"type": "done", "data": {
            "scan_run_id": scan_run_id,
            "total":       len(symbols),
            "completed":   len(results),
            "bullish":     bullish,
            "duration_s":  round(time.time() - start_time, 1),
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
            text("""SELECT symbol, score, recommendation, latest_close, rsi,
                    momentum_5d, ma_trend, macd_trend, volume_spike, breakout,
                    in_watchlist, scanned_at
                    FROM scan_results WHERE scan_run_id = :rid ORDER BY score DESC"""),
            {"rid": run_id},
        ).fetchall()

        keys = ["symbol","score","recommendation","latest_close","rsi",
                "momentum_5d","ma_trend","macd_trend","volume_spike",
                "breakout","in_watchlist","scanned_at"]
        results = []
        for r in rows:
            d = dict(zip(keys, r))
            d["scanned_at"] = d["scanned_at"].isoformat() if d["scanned_at"] else None
            results.append(d)

        return {"scan_run_id": run_id, "scanned_at": results[0]["scanned_at"] if results else None, "results": results}
    finally:
        db.close()


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": "scanner-service"}