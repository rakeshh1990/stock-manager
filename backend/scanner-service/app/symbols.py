# ---------------------------------------------------------------------------
# NSE symbol universe — updated May 2026
#
# Key corporate actions reflected:
#   TATAMOTORS demerged Oct 2025 → TMPV (passenger) + TMCV (commercial)
#   LTIM renamed to LTM (Feb 2026) after LTIMindtree → LTM Limited
#   INFOSYS trades as INFY on NSE Bhavcopy
#
# All symbols are bare NSE tickers as they appear in Bhavcopy CSV (no .NS suffix).
# The scanner strips .NS before querying market-service.
# ---------------------------------------------------------------------------

NIFTY_50 = [
    "RELIANCE",   "TCS",        "HDFCBANK",   "BHARTIARTL", "TMPV",
    "ICICIBANK",  "INFY",       "SBIN",       "HINDUNILVR", "ITC",
    "LT",         "KOTAKBANK",  "AXISBANK",   "HCLTECH",    "ASIANPAINT",
    "MARUTI",     "SUNPHARMA",  "TITAN",      "BAJFINANCE", "WIPRO",
    "ONGC",       "NTPC",       "POWERGRID",  "ULTRACEMCO", "TECHM",
    "NESTLEIND",  "COALINDIA",  "M&M",        "BAJAJFINSV", "TMCV",
    "ADANIPORTS", "HINDALCO",   "GRASIM",     "DRREDDY",    "DIVISLAB",
    "CIPLA",      "EICHERMOT",  "APOLLOHOSP", "TATACONSUM", "HEROMOTOCO",
    "SBILIFE",    "HDFCLIFE",   "BPCL",       "BRITANNIA",  "INDUSINDBK",
    "BAJAJ-AUTO", "TATASTEEL",  "ADANIENT",   "LTM",        "SHRIRAMFIN",
]

NIFTY_NEXT_50 = [
    "SIEMENS",    "PIDILITIND", "DMART",      "ICICIPRULI", "SBICARD",
    "GODREJCP",   "BERGEPAINT", "TORNTPHARM", "TRENT",      "COLPAL",
    "MUTHOOTFIN", "DABUR",      "MARICO",     "ICICIGI",    "HAVELLS",
    "INDIGO",     "BOSCHLTD",   "CHOLAFIN",   "LUPIN",      "BIOCON",
    "MOTHERSON",  "OFSS",       "AMBUJACEM",  "NAUKRI",     "GUJGASLTD",
    "SRF",        "MCDOWELL-N", "PIIND",      "AUROPHARMA", "PGHH",
    "INDHOTEL",   "VOLTAS",     "ALKEM",      "BANDHANBNK", "PFC",
    "RECLTD",     "ABB",        "CONCOR",     "PAGEIND",    "OBEROIRLTY",
    "ASTRAL",     "PERSISTENT", "COFORGE",    "TATACOMM",   "BALKRISIND",
    "FEDERALBNK", "SUNDARMFIN", "ZYDUSLIFE",  "ABCAPITAL",  "GMRINFRA",
]

NIFTY_100 = NIFTY_50 + NIFTY_NEXT_50

SCAN_SCOPES = {
    "nifty50":  NIFTY_50,
    "nifty100": NIFTY_100,
}