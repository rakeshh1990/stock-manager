# main.py
import logging
import yfinance as yf
from nsetools import Nse
import pandas as pd
import os

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
    logging.info(f"✅ Analysing : {symbol} ")
    try:
        # Download 5-day data for momentum
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
        # print(df)
        if df is None or df.empty or df.shape[0] < 2:
            raise ValueError(f"Not enough data to analyze {symbol}")

        latest_close = df['Close'].iloc[-1].item()
        previous_close = df['Close'].iloc[-2].item()
        momentum = ((latest_close - previous_close) / previous_close) * 100

        # Average volume over the last 5 days
        avg_volume = int(df['Volume'].mean().item()) if 'Volume' in df.columns else 0

        # Download 30-day data for MA trend
        df_full = yf.download(symbol, period="30d", interval="1d", progress=False, auto_adjust=True)
        if df_full is None or df_full.empty or 'Close' not in df_full.columns:
            raise ValueError(f"No valid Close data for {symbol}")

        ma20 = df_full['Close'].rolling(window=20).mean()
        ma_values = ma20.dropna()

        if len(ma_values) >= 2:
            ma_downtrend = ma_values.iloc[-1].item() < ma_values.iloc[-2].item()
            ma_uptrend = ma_values.iloc[-1].item() > ma_values.iloc[-2].item()
        else:
            ma_downtrend = False
            ma_uptrend = False

        return {
            'symbol': symbol,
            'momentum': momentum,
            'avg_volume': avg_volume,
            'ma_downtrend': ma_downtrend,
            'ma_uptrend': ma_uptrend
        }

    except Exception as e:
        logging.warning(f"⚠️ Failed to analyze {symbol}: {e}")
        return {
            'symbol': symbol,
            'momentum': 0,
            'avg_volume': 0,
            'ma_downtrend': False,
            'ma_uptrend': False
        }


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
            if result['momentum'] < MOMENTUM_LOSS_THRESHOLD or result['ma_downtrend']:
                logging.warning(
                    f"⚠️ {stock} may be losing momentum. 5D Change: {result['momentum']:.2f}%, Downtrend: {result['ma_downtrend']}"
                )
            else:
                logging.info(f"✅ {stock} still strong: +{result['momentum']:.2f}%")

if __name__ == '__main__':
    main()