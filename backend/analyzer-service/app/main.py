from fastapi import FastAPI
from typing import Dict

app = FastAPI(title="Analyzer Service")

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
