import os
import io
import time
import logging
import zipfile
import requests
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
import threading

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from .database import SessionLocal, engine
from .models import Base, PriceHistory, BhavCopyRun

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("market-service")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Market Service", version="1.0.0")

# ---------------------------------------------------------------------------
# Bhavcopy ingestion
# ---------------------------------------------------------------------------
# NSE publishes a Bhavcopy zip every trading day after ~4 PM IST.
# One request = OHLCV for all 2000+ NSE-listed stocks.
# Format: CM-DDMmmYYYY-bhav.csv.zip
# No API key, no rate limiting, official NSE data.

BHAVCOPY_URL = (
    "https://nsearchives.nseindia.com/content/cm/"
    "BhavCopy_BSE_CM_0_0_0_{date}_F_0000.csv.zip"
)

# Fallback URL pattern (older NSE format)
BHAVCOPY_URL_ALT = (
    "https://www1.nseindia.com/content/historical/EQUITIES/"
    "{year}/{month}/cm{date}bhav.csv.zip"
)

# Session with browser headers — NSE blocks plain urllib requests
_NSE_SESSION = requests.Session()
_NSE_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer":         "https://www.nseindia.com/",
})


def _trading_days_back(n: int = 5) -> list:
    """Return last n weekdays (Mon-Fri) going back from today."""
    days = []
    d = date.today()
    while len(days) < n:
        if d.weekday() < 5:   # Mon-Fri
            days.append(d)
        d -= timedelta(days=1)
    return days


def _fetch_bhavcopy(trade_date: date) -> Optional[pd.DataFrame]:
    """
    Download and parse NSE Bhavcopy CSV for the given trade date.
    Returns a DataFrame with columns: symbol, open, high, low, close, volume, series.
    Returns None if the file is not available (holiday or weekend).
    """
    date_str  = trade_date.strftime("%d%b%Y").upper()   # e.g. 15MAY2025
    month_str = trade_date.strftime("%b").upper()        # e.g. MAY
    year_str  = trade_date.strftime("%Y")

    urls = [
        f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{trade_date.strftime('%Y%m%d')}_F_0000.csv.zip",
        f"https://www1.nseindia.com/content/historical/EQUITIES/{year_str}/{month_str}/cm{date_str}bhav.csv.zip",
    ]

    for url in urls:
        try:
            logger.info(f"Fetching Bhavcopy from: {url}")
            # Hit NSE homepage first to get session cookies
            _NSE_SESSION.get("https://www.nseindia.com", timeout=10)
            r = _NSE_SESSION.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                zf  = zipfile.ZipFile(io.BytesIO(r.content))
                csv = zf.read(zf.namelist()[0]).decode("utf-8")
                df  = pd.read_csv(io.StringIO(csv))
                logger.info(f"Bhavcopy downloaded: {len(df)} rows for {trade_date}")
                return df
        except Exception as e:
            logger.warning(f"URL failed ({url}): {e}")
            continue

    logger.warning(f"No Bhavcopy available for {trade_date} (holiday or weekend)")
    return None


def _normalise_bhavcopy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise column names across different NSE Bhavcopy CSV formats.
    NSE has changed their format multiple times — handle both old and new.
    """
    df.columns = [c.strip().upper() for c in df.columns]

    col_map = {}
    # Symbol
    for c in ["SYMBOL", "TckrSymb", "TCKRSYMB"]:
        if c.upper() in df.columns:
            col_map["symbol"] = c.upper(); break
    # Series
    for c in ["SERIES", "SctySrs", "SCTYSRS"]:
        if c.upper() in df.columns:
            col_map["series"] = c.upper(); break
    # OHLCV
    for src, dst in [
        (["OPEN", "OpnPric", "OPNPRIC"], "open"),
        (["HIGH", "HghPric", "HGHPRIC"], "high"),
        (["LOW",  "LwPric",  "LWPRIC"],  "low"),
        (["CLOSE","ClsPric", "CLSPRIC"], "close"),
        (["TOTTRDQTY","TtlTradgVol","TTLTRADGVOL","VOLUME"], "volume"),
    ]:
        for c in src:
            if c.upper() in df.columns:
                col_map[dst] = c.upper(); break

    if "symbol" not in col_map or "close" not in col_map:
        raise ValueError(f"Could not map required columns. Available: {list(df.columns)}")

    result = pd.DataFrame()
    result["symbol"] = df[col_map["symbol"]].str.strip()
    result["series"] = df[col_map.get("series", "symbol")].str.strip() if "series" in col_map else "EQ"
    result["open"]   = pd.to_numeric(df[col_map["open"]],   errors="coerce") if "open"   in col_map else None
    result["high"]   = pd.to_numeric(df[col_map["high"]],   errors="coerce") if "high"   in col_map else None
    result["low"]    = pd.to_numeric(df[col_map["low"]],    errors="coerce") if "low"    in col_map else None
    result["close"]  = pd.to_numeric(df[col_map["close"]],  errors="coerce")
    result["volume"] = pd.to_numeric(df[col_map["volume"]], errors="coerce") if "volume" in col_map else None

    # Keep only EQ series (regular equity) — skip futures, options, SME
    result = result[result["series"] == "EQ"].copy()
    result = result.dropna(subset=["symbol", "close"])
    return result


def ingest_bhavcopy(trade_date: date) -> dict:
    """
    Download, parse, and persist Bhavcopy for the given trade date.
    Idempotent — skips if already ingested for that date.
    """
    db = SessionLocal()
    try:
        # Check if already ingested
        existing = db.execute(
            text("""
                SELECT status
                FROM bhavcopy_runs
                WHERE trade_date = :d
            """),
            {"d": trade_date}
        ).fetchone()


        if existing:
            logger.info(
                f"Bhavcopy for {trade_date} already processed ({existing[0]}) - skipping"
            )

            return {
                "status": "skipped",
                "trade_date": str(trade_date)
            }

        raw_df = _fetch_bhavcopy(trade_date)
        if raw_df is None:
            db.add(BhavCopyRun(trade_date=trade_date, status="skipped", rows_inserted=0))
            db.commit()
            return {"status": "skipped", "trade_date": str(trade_date)}

        df = _normalise_bhavcopy(raw_df)
        inserted = 0

        for _, row in df.iterrows():
            try:
                db.execute(
                    text("""
                        INSERT INTO price_history
                            (symbol, trade_date, open, high, low, close, volume, series)
                        VALUES
                            (:symbol, :trade_date, :open, :high, :low, :close, :volume, :series)
                        ON CONFLICT (symbol, trade_date) DO UPDATE SET
                            open   = EXCLUDED.open,
                            high   = EXCLUDED.high,
                            low    = EXCLUDED.low,
                            close  = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    """),
                    {
                        "symbol":     row["symbol"],
                        "trade_date": trade_date,
                        "open":       row.get("open"),
                        "high":       row.get("high"),
                        "low":        row.get("low"),
                        "close":      row["close"],
                        "volume":     row.get("volume"),
                        "series":     row.get("series", "EQ"),
                    }
                )
                inserted += 1
            except Exception as e:
                logger.warning(f"Row insert failed for {row.get('symbol')}: {e}")

        db.add(BhavCopyRun(
            trade_date=trade_date,
            status="success",
            rows_inserted=inserted,
        ))
        db.commit()
        logger.info(f"Bhavcopy ingested for {trade_date}: {inserted} rows")
        return {"status": "success", "trade_date": str(trade_date), "rows": inserted}

    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"status": "failed", "trade_date": str(trade_date), "error": str(e)}
    finally:
        db.close()


def _scheduled_ingest():

    logger.info("Scheduled reconciliation started")

    for d in _trading_days_back(90):
        ingest_bhavcopy(d)

    logger.info("Scheduled reconciliation completed")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup():

    def reconcile():
        logger.info("Reconciling last 90 days")

        for d in _trading_days_back(90):
            ingest_bhavcopy(d)

        logger.info("Reconciliation completed")


    threading.Thread(
        target=reconcile,
        daemon=True
    ).start()


    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    scheduler.add_job(
        _scheduled_ingest,
        CronTrigger(hour=16, minute=15)
    )

    scheduler.start()


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

class PricePoint(BaseModel):
    date:   str
    open:   Optional[float]
    high:   Optional[float]
    low:    Optional[float]
    close:  float
    volume: Optional[float]


@app.get("/history/{symbol}", response_model=List[PricePoint])
def get_history(
    symbol: str,
    days:   int = Query(default=130, ge=1, le=500),
):
    """
    Return daily OHLCV for a symbol for the last N trading days.
    Used by analyzer-service and scanner-service — no external API calls.
    """
    symbol = symbol.strip().upper()
    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT trade_date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = :sym
                ORDER BY trade_date DESC
                LIMIT :days
            """),
            {"sym": symbol, "days": days}
        ).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No price data for {symbol}")
        return [
            PricePoint(
                date=str(r[0]),
                open=r[1], high=r[2], low=r[3],
                close=r[4], volume=r[5],
            )
            for r in reversed(rows)   # chronological order
        ]
    finally:
        db.close()


@app.get("/history/{symbol}/latest")
def get_latest(symbol: str):
    """Return just the latest closing price for a symbol."""
    symbol = symbol.strip().upper()
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT trade_date, close, volume
                FROM price_history
                WHERE symbol = :sym
                ORDER BY trade_date DESC LIMIT 1
            """),
            {"sym": symbol}
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        return {"symbol": symbol, "date": str(row[0]), "close": row[1], "volume": row[2]}
    finally:
        db.close()


@app.get("/history/index/nifty50")
def get_nifty50_history(days: int = Query(default=252, ge=1, le=500)):
    """
    Return daily closing prices for the Nifty 50 index.
    Used by the login page chart — replaces the old yfinance call.
    """
    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT trade_date, close
                FROM price_history
                WHERE symbol = 'NIFTY 50'
                ORDER BY trade_date DESC
                LIMIT :days
            """),
            {"days": days}
        ).fetchall()
        if not rows:
            # Fallback: compute synthetic Nifty from constituents average
            raise HTTPException(status_code=404, detail="Nifty 50 index data not yet available")
        return [{"date": str(r[0]), "close": r[1]} for r in reversed(rows)]
    finally:
        db.close()


@app.post("/ingest/manual")
def manual_ingest(trade_date: Optional[str] = None):
    """
    Manually trigger Bhavcopy ingestion for a specific date.
    Useful for backfilling missed days. Format: YYYY-MM-DD
    """
    if trade_date:
        d = date.fromisoformat(trade_date)
    else:
        d = date.today()
    result = ingest_bhavcopy(d)
    return result


@app.get("/ingest/status")
def ingest_status(limit: int = 10):
    """Return the last N ingestion run statuses."""
    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT trade_date, status, rows_inserted, error, ran_at
                FROM bhavcopy_runs
                ORDER BY trade_date DESC
                LIMIT :limit
            """),
            {"limit": limit}
        ).fetchall()
        return [
            {
                "trade_date":    str(r[0]),
                "status":        r[1],
                "rows_inserted": r[2],
                "error":         r[3],
                "ran_at":        r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    finally:
        db.close()



# ---------------------------------------------------------------------------
# Index constituents — fetched from NSE and cached in memory
# NSE publishes index composition CSV daily at:
# https://nseindia.com/content/indices/ind_nifty50list.csv
# https://nseindia.com/content/indices/ind_niftynext50list.csv
# This means symbols are always current — no hardcoded lists to maintain.
# ---------------------------------------------------------------------------

_CONSTITUENTS_CACHE: dict = {}   # { "nifty50": (fetched_at, [symbols]) }
_CONSTITUENTS_TTL   = 6 * 3600  # 6 hours — index composition changes quarterly

INDEX_URLS = {
    "nifty50":   "https://nseindia.com/content/indices/ind_nifty50list.csv",
    "nifty100":  "https://nseindia.com/content/indices/ind_nifty100list.csv",
    "niftynext50": "https://nseindia.com/content/indices/ind_niftynext50list.csv",
}

# Fallback hardcoded lists — used only if NSE fetch fails
_FALLBACK_NIFTY50 = [
    "RELIANCE","TCS","HDFCBANK","BHARTIARTL","TMPV","ICICIBANK","INFY","SBIN",
    "HINDUNILVR","ITC","LT","KOTAKBANK","AXISBANK","HCLTECH","ASIANPAINT",
    "MARUTI","SUNPHARMA","TITAN","BAJFINANCE","WIPRO","ONGC","NTPC","POWERGRID",
    "ULTRACEMCO","TECHM","NESTLEIND","COALINDIA","M&M","BAJAJFINSV","TMCV",
    "ADANIPORTS","HINDALCO","GRASIM","DRREDDY","DIVISLAB","CIPLA","EICHERMOT",
    "APOLLOHOSP","TATACONSUM","HEROMOTOCO","SBILIFE","HDFCLIFE","BPCL",
    "BRITANNIA","INDUSINDBK","BAJAJ-AUTO","TATASTEEL","ADANIENT","LTM","SHRIRAMFIN",
]

_FALLBACK_NIFTYNEXT50 = [
    "SIEMENS","PIDILITIND","DMART","ICICIPRULI","SBICARD","GODREJCP","BERGEPAINT",
    "TORNTPHARM","TRENT","COLPAL","MUTHOOTFIN","DABUR","MARICO","ICICIGI","HAVELLS",
    "INDIGO","BOSCHLTD","CHOLAFIN","LUPIN","BIOCON","MOTHERSON","OFSS","AMBUJACEM",
    "NAUKRI","GUJGASLTD","SRF","MCDOWELL-N","PIIND","AUROPHARMA","PGHH","INDHOTEL",
    "VOLTAS","ALKEM","BANDHANBNK","PFC","RECLTD","ABB","CONCOR","PAGEIND",
    "OBEROIRLTY","ASTRAL","PERSISTENT","COFORGE","TATACOMM","BALKRISIND",
    "FEDERALBNK","SUNDARMFIN","ZYDUSLIFE","ABCAPITAL","GMRINFRA",
]


def _fetch_constituents_from_nse(index: str) -> list:
    """
    Fetch current index constituents CSV from NSE.
    Returns list of bare NSE symbols matching Bhavcopy format.
    """
    url = INDEX_URLS.get(index)
    if not url:
        raise ValueError(f"Unknown index: {index}")

    # Hit NSE homepage first for session cookie
    _NSE_SESSION.get("https://www.nseindia.com", timeout=10)
    r = _NSE_SESSION.get(url, timeout=15)
    r.raise_for_status()

    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]

    # NSE CSV has a "Symbol" column
    symbol_col = next((c for c in df.columns if c.upper() == "SYMBOL"), None)
    if not symbol_col:
        raise ValueError(f"No Symbol column found. Columns: {list(df.columns)}")

    symbols = [s.strip().upper() for s in df[symbol_col].tolist() if str(s).strip()]
    logger.info(f"Fetched {len(symbols)} constituents for {index} from NSE")
    return symbols


def get_constituents(index: str) -> list:
    """
    Return current index constituents, using cache if fresh.
    Falls back to hardcoded list if NSE fetch fails.
    """
    now = time.time()
    cached = _CONSTITUENTS_CACHE.get(index)
    if cached and (now - cached["fetched_at"]) < _CONSTITUENTS_TTL:
        return cached["symbols"]

    try:
        symbols = _fetch_constituents_from_nse(index)
        _CONSTITUENTS_CACHE[index] = {"symbols": symbols, "fetched_at": now}
        return symbols
    except Exception as e:
        logger.warning(f"NSE constituents fetch failed for {index}: {e} — using fallback")
        if index == "nifty50":
            return _FALLBACK_NIFTY50
        elif index in ("niftynext50", "nifty100"):
            next50 = _FALLBACK_NIFTYNEXT50
            return (_FALLBACK_NIFTY50 + next50) if index == "nifty100" else next50
        return []


@app.get("/constituents/{index}")
def constituents(index: str):
    """
    Return current NSE index constituents.
    Supported: nifty50, nifty100, niftynext50
    Fetched live from NSE and cached for 6 hours.
    """
    valid = {"nifty50", "nifty100", "niftynext50"}
    if index not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown index. Valid: {valid}")

    symbols = get_constituents(index)
    return {
        "index":   index,
        "count":   len(symbols),
        "symbols": symbols,
        "cached":  index in _CONSTITUENTS_CACHE,
        "source":  "nse_live" if index in _CONSTITUENTS_CACHE else "fallback",
    }


@app.post("/constituents/refresh")
def refresh_constituents():
    """Force-clear the constituents cache — triggers fresh NSE fetch on next call."""
    _CONSTITUENTS_CACHE.clear()
    return {"status": "cache cleared"}

@app.get("/health", tags=["ops"])
def health():
    db = SessionLocal()
    try:
        count = db.execute(text("SELECT COUNT(*) FROM price_history")).scalar()
        latest = db.execute(
            text("SELECT MAX(trade_date) FROM price_history")
        ).scalar()
        return {
            "status":      "ok",
            "service":     "market-service",
            "total_rows":  count,
            "latest_date": str(latest) if latest else None,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
    finally:
        db.close()