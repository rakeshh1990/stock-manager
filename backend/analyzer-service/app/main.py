# from fastapi import FastAPI
from typing import Dict

# app = FastAPI(title="Analyzer Service")


# backend/analyzer-service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Optional
import os
from nsetools import Nse
from datetime import datetime

# try to import ta; if missing later pip will install
from ta.momentum import RSIIndicator
from ta.trend import MACD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)
nse = Nse()

app = FastAPI(title="Analyzer Service", version="1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "analyzer"}

@app.get("/analyze")
def analyze(symbol: str = "RELIANCE.NS") -> Dict:
    # Stubbed response; integrate yfinance later.
    return {
        "symbol": symbol,
        "momentum": 2.7,
        "rsi": 54.2,
        "macd_bullish": True,
        "near_52w_high": False,
        "near_52w_low": False,
        "breakout": False
    }

# --- Response models
class AnalysisResult(BaseModel):
    symbol: str
    latest_close: float
    date: str
    momentum_5d_pct: float
    ma50: Optional[float]
    ma200: Optional[float]
    ma_trend: Optional[str]
    rsi: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_trend: Optional[str]
    near_52w_high: bool
    near_52w_low: bool
    pct_from_52w_high: float
    pct_from_52w_low: float
    avg_volume_20: Optional[int]
    recent_volume: Optional[int]
    volume_spike: bool
    price_breakout_20: bool
    breakout_confirmed: bool
    score: int
    recommendation: str
    note: Optional[str] = None

# --- Helpers
def safe_last(ser):
    """Return last value or None"""
    return None if ser is None or ser.empty else float(ser.iloc[-1])

def fetch_history(symbol: str, period: str = "1y", interval: str = "1d"):
    """Fetch historical price data via yfinance."""
    # yfinance returns DataFrame with DatetimeIndex
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError("No data returned from yfinance for symbol: " + symbol)
    return df

def compute_indicators(df: pd.DataFrame):
    """Compute indicators: RSI(14), MACD, MA50, MA200, volumes etc."""
    out = {}

    # Ensure we have enough rows
    n = df.shape[0]
    out['enough_history'] = n >= 30

    # Latest close and date
    latest_close = float(df['Close'].iloc[-1])
    latest_date = str(df.index[-1].date())

    # Momentum 5-day pct (using close 5 trading days ago)
    if n >= 6:
        prev_5 = float(df['Close'].iloc[-6])
        momentum_5d = ((latest_close - prev_5) / prev_5) * 100
    else:
        momentum_5d = 0.0

    # Moving averages
    ma50 = df['Close'].rolling(window=50).mean() if n >= 50 else df['Close'].rolling(window=min(20, n)).mean()
    ma200 = df['Close'].rolling(window=200).mean() if n >= 200 else df['Close'].rolling(window=min(100, n)).mean()

    ma50_last = safe_last(ma50)
    ma200_last = safe_last(ma200)

    if ma50_last is not None and ma200_last is not None:
        ma_trend = "bull" if ma50_last > ma200_last else "bear"
    else:
        ma_trend = None

    # RSI (14)
    try:
        rsi_ind = RSIIndicator(close=df['Close'], window=14)
        rsi = safe_last(rsi_ind.rsi())
    except Exception:
        rsi = None

    # MACD
    try:
        macd_ind = MACD(close=df['Close'])
        macd = safe_last(macd_ind.macd())
        macd_signal = safe_last(macd_ind.macd_signal())
        if macd is not None and macd_signal is not None:
            macd_trend = "bull" if macd > macd_signal else "bear"
        else:
            macd_trend = None
    except Exception:
        macd = macd_signal = None
        macd_trend = None

    # 52-week high/low (approx from 1y range)
    high_52w = float(df['Close'].max())
    low_52w = float(df['Close'].min())
    pct_from_high = (high_52w - latest_close) / high_52w * 100 if high_52w > 0 else 0.0
    pct_from_low = (latest_close - low_52w) / low_52w * 100 if low_52w > 0 else 0.0
    near_52w_high = pct_from_high <= 5.0  # within 5%
    near_52w_low = pct_from_low <= 5.0

    # Volume stats
    avg_vol_20 = int(df['Volume'].tail(20).mean()) if 'Volume' in df.columns and n >= 5 else None
    recent_vol = int(df['Volume'].iloc[-1]) if 'Volume' in df.columns else None
    volume_spike = False
    if avg_vol_20 and recent_vol:
        volume_spike = recent_vol > avg_vol_20 * 1.5

    # Price breakout (20-day)
    try:
        rolling20_max = df['Close'].rolling(window=20).max()
        # Compare against previous window max (exclude today)
        price_breakout = latest_close > (rolling20_max.iloc[-2] if len(rolling20_max) >= 2 else rolling20_max.iloc[-1])
    except Exception:
        price_breakout = False

    # Breakout confirmed if both price_breakout and volume_spike
    breakout_confirmed = price_breakout and volume_spike

    out.update({
        'latest_close': latest_close,
        'latest_date': latest_date,
        'momentum_5d': momentum_5d,
        'ma50': ma50_last,
        'ma200': ma200_last,
        'ma_trend': ma_trend,
        'rsi': rsi,
        'macd': macd,
        'macd_signal': macd_signal,
        'macd_trend': macd_trend,
        'high_52w': high_52w,
        'low_52w': low_52w,
        'pct_from_high': pct_from_high,
        'pct_from_low': pct_from_low,
        'near_52w_high': near_52w_high,
        'near_52w_low': near_52w_low,
        'avg_vol_20': avg_vol_20,
        'recent_vol': recent_vol,
        'volume_spike': volume_spike,
        'price_breakout': price_breakout,
        'breakout_confirmed': breakout_confirmed
    })

    return out

def score_and_recommend(ind: dict):
    """Simple scoring system that returns integer score and recommendation string."""
    score = 0
    reasons = []

    # momentum
    if ind['momentum_5d'] >= 3:
        score += 2
        reasons.append("5d momentum strong")
    elif ind['momentum_5d'] > 0:
        score += 1

    # MA trend
    if ind['ma_trend'] == "bull":
        score += 2
        reasons.append("MA50 > MA200")
    elif ind['ma_trend'] == "bear":
        score -= 1

    # RSI
    rsi = ind.get('rsi')
    if rsi is not None:
        if rsi < 30:
            score += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI overbought")

    # MACD
    if ind.get('macd_trend') == "bull":
        score += 1
    elif ind.get('macd_trend') == "bear":
        score -= 1

    # 52w proximity: closer to high => less bullish score (contrarian)
    if ind['near_52w_low']:
        score += 1
    if ind['near_52w_high']:
        score -= 1

    # breakout
    if ind['breakout_confirmed']:
        score += 2
        reasons.append("breakout confirmed (price + volume)")
    elif ind['price_breakout']:
        score += 1

    # volume
    if ind.get('volume_spike'):
        score += 1

    # Recommendation
    if score >= 4:
        rec = "STRONG BUY"
    elif score >= 2:
        rec = "BUY"
    elif score >= 0:
        rec = "HOLD"
    else:
        rec = "SELL"

    return int(score), rec, "; ".join(reasons) if reasons else None

def get_stock_data(symbol: str):
    """
    Fetch stock data with fallback:
      1️⃣ Try Yahoo Finance (via yfinance)
      2️⃣ Fallback to NSE (for Indian stocks)
    """
    # --- Try Yahoo Finance ---
    try:
        df = yf.download(symbol, period="1y", progress=False)
        if not df.empty:
            logger.info(f"Fetched {len(df)} records for {symbol} from Yahoo Finance")
            return df
        else:
            logger.warning(f"Yahoo returned empty for {symbol}, trying NSE fallback")
    except Exception as e:
        logger.error(f"Yahoo fetch error for {symbol}: {e}")

    # --- Try NSE Fallback (only works for Indian tickers) ---
    try:
        sym_clean = symbol.replace(".NS", "")
        quote = nse.get_quote(sym_clean)
        if quote:
            logger.info(f"Fetched {symbol} data from NSE fallback")
            # Construct minimal DataFrame for compatibility
            last_price = float(quote.get('lastPrice', 0))
            df = pd.DataFrame([{
                'Close': last_price,
                'Open': last_price,
                'High': last_price,
                'Low': last_price,
                'Volume': int(quote.get('quantityTraded', 0))
            }])
            df.index = pd.to_datetime([datetime.now()])
            df.index.name = "Date"
            return df
        else:
            logger.error(f"NSE returned empty for {symbol}")
    except Exception as e:
        logger.error(f"NSE fallback failed for {symbol}: {e}")

    # --- Total Failure ---
    logger.error(f"All data sources failed for {symbol}")
    return None

def sanitize_for_json(data):
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(v) for v in data]
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return 0.0
    return data

# --- Endpoint
@app.get("/analyse", response_model=AnalysisResult)
def analyse(symbol: str):
    symbol = symbol.strip().upper()
    logging.info(f"Analyse request for {symbol}")
    df = get_stock_data(symbol)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    try:
        ind = compute_indicators(df)
        ind = sanitize_for_json(ind)
    except Exception as e:
        logging.exception("Indicator computation failed")
        raise HTTPException(status_code=500, detail=str(e))

    score, rec, note = score_and_recommend(ind)

    result = AnalysisResult(
        symbol=symbol,
        latest_close=round(ind['latest_close'], 2),
        date=ind['latest_date'],
        momentum_5d_pct=round(ind['momentum_5d'], 2),
        ma50=round(ind['ma50'], 2) if ind['ma50'] is not None else None,
        ma200=round(ind['ma200'], 2) if ind['ma200'] is not None else None,
        ma_trend=ind['ma_trend'],
        rsi=round(ind['rsi'], 2) if ind['rsi'] is not None else None,
        macd=round(ind['macd'], 6) if ind['macd'] is not None else None,
        macd_signal=round(ind['macd_signal'], 6) if ind['macd_signal'] is not None else None,
        macd_trend=ind['macd_trend'],
        near_52w_high=ind['near_52w_high'],
        near_52w_low=ind['near_52w_low'],
        pct_from_52w_high=round(ind['pct_from_high'], 2),
        pct_from_52w_low=round(ind['pct_from_low'], 2),
        avg_volume_20=ind['avg_vol_20'],
        recent_volume=ind['recent_vol'],
        volume_spike=bool(ind['volume_spike']),
        price_breakout_20=bool(ind['price_breakout']),
        breakout_confirmed=bool(ind['breakout_confirmed']),
        score=score,
        recommendation=rec,
        note=note
    )
    return result
