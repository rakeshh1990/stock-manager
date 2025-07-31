# main.py
import logging
import yfinance as yf
from nsetools import Nse
import pandas as pd
import os
from ta.momentum import RSIIndicator
from ta.trend import MACD


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load invested stocks
def load_invested_stocks(file_path="invested_stocks.csv"):
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return []
    df = pd.read_csv(file_path)
    symbols = df['symbol'].tolist()
    logging.info(f"Loaded {len(symbols)} invested stocks from CSV.")
    return symbols

# Get Nifty 50 stocks (with fallback if nsetools fails)
def get_nifty_50_symbols():
    try:
        nse = Nse()
        codes = nse.get_stock_codes()
        logging.info('-------------------------------')
        logging.info(f"Loaded {len(codes)} stocks from NSE.")
        # logging.info(codes)
        if not isinstance(codes, list) or len(codes) < 10:
            raise ValueError("Unexpected format from nse.get_stock_codes()")

        # Remove header if present
        codes = [code for code in codes if code != 'SYMBOL']

        return [symbol + '.NS' for symbol in codes]
    except Exception as e:
        logging.warning("⚠️ Failed to fetch Nifty50 stocks from NSE: %s", str(e))
        # fallback list (partial for demo)
        return ['RELIANCE.NS', 'INFY.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']

# Compare and log price change
# Thresholds
MIN_VOLUME = 1_000_000
MOMENTUM_GAIN_THRESHOLD = 3.0  # 5-day positive change
MOMENTUM_LOSS_THRESHOLD = -1.0  # 5-day drop indicates weakness
nifty50_stocks = get_nifty_50_symbols()
invested_stocks = load_invested_stocks()

def analyze_stock(symbol):
    logging.info(f"✅ Analyzing: {symbol}")
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty or 'Close' not in df.columns or 'Volume' not in df.columns:
            raise ValueError(f"Incomplete data for {symbol}")

        close_series = df['Close'].squeeze()
        volume_series = df['Volume'].squeeze()

        # Momentum (5d)
        df_recent = df.tail(6)
        if len(df_recent) < 2:
            raise ValueError(f"Not enough recent data for momentum calc: {symbol}")
        momentum = ((df_recent['Close'].iloc[-1].item() - df_recent['Close'].iloc[-2].item()) / df_recent['Close'].iloc[-2].item()) * 100

        # Average Volume (5d)
        avg_volume = int(df_recent['Volume'].mean().item())

        # MA Trend (20-day)
        ma20 = close_series.rolling(window=20).mean()
        ma_downtrend = ma20.iloc[-1] < ma20.iloc[-2]
        ma_uptrend = ma20.iloc[-1] > ma20.iloc[-2]

        # RSI (14)
        rsi_indicator = RSIIndicator(close=close_series, window=14)
        rsi = rsi_indicator.rsi().iloc[-1]

        # MACD
        macd_indicator = MACD(close=close_series)
        macd = macd_indicator.macd().iloc[-1]
        macd_signal = macd_indicator.macd_signal().iloc[-1]
        macd_trend = macd > macd_signal  # True = bullish

        # 52-week High/Low Proximity
        high_52w = close_series.max()
        low_52w = close_series.min()
        current_price = close_series.iloc[-1]
        near_52w_high = (high_52w - current_price) / high_52w < 0.05  # within 5%
        near_52w_low = (current_price - low_52w) / low_52w < 0.05     # within 5%

        # Price-Volume Breakout Confirmation
        recent_volume = volume_series.iloc[-1]
        avg_vol_20 = volume_series.tail(20).mean()
        price_breakout = current_price > close_series.rolling(20).max().iloc[-2]
        volume_spike = recent_volume > avg_vol_20 * 1.5

        breakout_confirmed = price_breakout and volume_spike

        return {
            'symbol': symbol,
            'momentum': momentum,
            'avg_volume': avg_volume,
            'ma_uptrend': ma_uptrend,
            'ma_downtrend': ma_downtrend,
            'rsi': rsi,
            'macd_bullish': macd_trend,
            'near_52w_high': near_52w_high,
            'near_52w_low': near_52w_low,
            'breakout': breakout_confirmed
        }

    except Exception as e:
        logging.warning(f"⚠️ Failed to analyze {symbol}: {e}")
        return {
            'symbol': symbol,
            'momentum': 0,
            'avg_volume': 0,
            'ma_uptrend': False,
            'ma_downtrend': False,
            'rsi': 0,
            'macd_bullish': False,
            'near_52w_high': False,
            'near_52w_low': False,
            'breakout': False
        }

def print_analysis(result, is_invested=False):
    symbol = result['symbol']
    print(f"\n📊 Analysis for: {symbol}")
    print("-" * (16 + len(symbol)))

    # Calculate score for recommendation
    score = 0
    if result['momentum'] > 2:
        score += 1
    if result['ma_uptrend']:
        score += 1
    if result['rsi'] > 60:
        score += 1
    if result['macd_bullish']:
        score += 1
    if result['near_52w_high']:
        score += 1
    if result['breakout']:
        score += 1

    # 🔄 Recommendation Logic
    if is_invested:
        # For invested stocks: focus on signal changes
        print(f"🔹 Momentum: {result['momentum']:.2f}%")
        print(f"🔹 RSI: {result['rsi']:.2f}")
        print(f"🔹 Trend: {'Up' if result['ma_uptrend'] else 'Down' if result['ma_downtrend'] else 'Flat'}")
        print(f"🔹 MACD: {'Bullish' if result['macd_bullish'] else 'Bearish'}")
        print(f"🔹 Breakout: {'Yes' if result['breakout'] else 'No'}")
        print(f"🔹 52W Proximity: {'High' if result['near_52w_high'] else 'Low' if result['near_52w_low'] else 'Neutral'}")

        if result['momentum'] < -2 or result['rsi'] < 35 or not result['ma_uptrend']:
            recommendation = "🔻 Suggestion: Consider SELLING or booking profits"
        elif result['momentum'] > 2 and result['rsi'] > 60 and result['ma_uptrend'] and result['macd_bullish']:
            recommendation = "🔼 Suggestion: Add / BUY on dips"
        else:
            recommendation = "➖ Suggestion: HOLD"
    else:
        # For new stocks: detailed analysis + score-based recommendation
        print(f"🔹 Momentum (5d): {result['momentum']:.2f}%")
        print(f"🔹 Avg Volume (5d): {result['avg_volume']:,}")

        # Trend
        trend = "📈 Uptrend" if result['ma_uptrend'] else "📉 Downtrend" if result['ma_downtrend'] else "➡️ Flat"
        print(f"🔹 20d MA Trend: {trend}")

        # RSI
        rsi_label = "🟢 Bullish" if result['rsi'] > 60 else "🟡 Neutral" if 40 <= result['rsi'] <= 60 else "🔴 Bearish"
        print(f"🔹 RSI (14): {result['rsi']:.2f} {rsi_label}")

        # MACD
        print(f"🔹 MACD: {'🟢 Bullish Crossover' if result['macd_bullish'] else '🔴 Bearish'}")

        # 52-week high/low
        print(f"🔹 Near 52-Week High: {'✅ Yes' if result['near_52w_high'] else '❌ No'}")
        print(f"🔹 Near 52-Week Low: {'⚠️ Yes' if result['near_52w_low'] else '❌ No'}")

        # Breakout
        print(f"🔹 Price-Volume Breakout: {'🚀 Confirmed' if result['breakout'] else '❌ No Breakout'}")

        # Final Recommendation
        if score >= 4:
            recommendation = "✅ Recommendation: STRONG BUY 🔼"
        elif 2 <= score < 4:
            recommendation = "🟡 Recommendation: HOLD ➖"
        else:
            recommendation = "🔻 Recommendation: AVOID / No Entry"
    
    print("-" * (16 + len(symbol)))
    print(recommendation)
    print("=" * (18 + len(symbol)))


def main():
    logging.info("🚀 Starting Momentum Scanner")

    # Scan Nifty 50 for new momentum opportunities
    logging.info("\n🔎 Scanning Nifty 50 for Momentum Opportunities...")
    opportunities = []
    for stock in nifty50_stocks:
        if stock in invested_stocks:
            continue
        result = analyze_stock(stock)
        if result:
            if (
                result['momentum'] >= MOMENTUM_GAIN_THRESHOLD
                and result['avg_volume'] >= MIN_VOLUME
                and result['ma_uptrend']
            ):
                opportunities.append((stock, result['momentum']))
                logging.info(f"💡 Potential Buy: {stock} => {result['momentum']:.2f}%")
                print_analysis(result, is_invested=False)

    # Show top 5 opportunities
    opportunities.sort(key=lambda x: x[1], reverse=True)
    logging.info("\n🔥 Top Momentum Stocks:")
    for stock, change in opportunities[:5]:
        logging.info(f"✅ {stock}: +{change:.2f}% (5-day)")

    logging.info("\n✅ Analysis Complete.")

    # Check for invested stocks losing momentum
    logging.info("\n🔻 Checking Invested Stocks for Momentum Drop...")
    for stock in invested_stocks:
        result = analyze_stock(stock)
        if result:
            print_analysis(result, is_invested=True)
            if result['momentum'] < MOMENTUM_LOSS_THRESHOLD or result['ma_downtrend']:
                logging.warning(
                    f"⚠️ {stock} may be losing momentum. 5D Change: {result['momentum']:.2f}%, Downtrend: {result['ma_downtrend']}"
                )
            else:
                logging.info(f"✅ {stock} still strong: +{result['momentum']:.2f}%")

if __name__ == '__main__':
    main()