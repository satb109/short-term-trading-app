"""
RSI(20) Upward-Crossover Check
------------------------------
Checks a fixed list of NSE-listed stocks and PRINTS to the console the ones
whose 14-period RSI has just crossed UP through 20 (i.e. yesterday's RSI was
below 20 and today's RSI is at/above 20 - a classic "exiting oversold" signal).

Run it any time with: python rsi_alert.py

If scheduled via GitHub Actions, the output shows up in that run's log under
the Actions tab (not on your local screen) - see the README for details.
"""

import sys
from datetime import datetime

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# NIFTY 50 ticker -> display name. yfinance needs the ".NS" suffix for NSE stocks.
TICKERS = {
    "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports and Special Economic Zone",
    "APOLLOHOSP.NS": "Apollo Hospitals Enterprise",
    "ASIANPAINT.NS": "Asian Paints",
    "AXISBANK.NS": "Axis Bank",
    "BAJAJAUTO.NS": "Bajaj Auto",
    "BAJFINANCE.NS": "Bajaj Finance",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "BPCL.NS": "Bharat Petroleum",
    "BHARTIARTL.NS": "Bharti Airtel",
    "BRITANNIA.NS": "Britannia Industries",
    "CIPLA.NS": "Cipla",
    "COALINDIA.NS": "Coal India",
    "DIVISLAB.NS": "Divi's Laboratories",
    "DRREDDY.NS": "Dr. Reddy's Laboratories",
    "EICHERMOT.NS": "Eicher Motors",
    "GRASIM.NS": "Grasim Industries",
    "HCLTECH.NS": "HCL Technologies",
    "HDFCBANK.NS": "HDFC Bank",
    "HDFCLIFE.NS": "HDFC Life",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "HINDALCO.NS": "Hindalco Industries",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ICICIBANK.NS": "ICICI Bank",
    "ITC.NS": "ITC",
    "INDUSINDBK.NS": "IndusInd Bank",
    "INFY.NS": "Infosys",
    "JSWSTEEL.NS": "JSW Steel",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen & Toubro",
    "M&M.NS": "Mahindra & Mahindra",
    "MARUTI.NS": "Maruti Suzuki",
    "NTPC.NS": "NTPC",
    "NESTLEIND.NS": "Nestle India",
    "ONGC.NS": "Oil and Natural Gas Corporation",
    "POWERGRID.NS": "Power Grid Corporation of India",
    "RELIANCE.NS": "Reliance Industries",
    "SBILIFE.NS": "SBI Life Insurance",
    "SHRIRAMFIN.NS": "Shriram Finance",
    "SUNPHARMA.NS": "Sun Pharmaceutical Industries",
    "TATACONSUM.NS": "Tata Consumer Products",
    "TATAMOTORS.NS": "Tata Motors",
    "TATASTEEL.NS": "Tata Steel",
    "TCS.NS": "Tata Consultancy Services",
    "TECHM.NS": "Tech Mahindra",
    "TITAN.NS": "Titan Company",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "UPL.NS": "UPL",
    "WIPRO.NS": "Wipro",
}

RSI_PERIOD = 14
RSI_THRESHOLD = 30


# ---------------------------------------------------------------------------
# RSI calculation (Wilder's smoothing - the standard/original RSI method)
# ---------------------------------------------------------------------------

def compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def check_ticker(ticker: str) -> dict | None:
    """Returns a dict with rsi info if data was usable, else None."""
    # 3 months of daily data comfortably covers the 14-period warm-up
    data = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)

    if data.empty:
        print(f"[WARN] No data returned for {ticker}, skipping.")
        return None

    close_col = None
    if "Close" in data:
        close_col = data["Close"]
    elif isinstance(data.columns, pd.MultiIndex) and ("Close", ticker) in data.columns:
        close_col = data[("Close", ticker)]
    elif isinstance(data.columns, pd.MultiIndex) and ("Close", slice(None)) in data.columns:
        close_col = data["Close"].iloc[:, 0]

    if close_col is None:
        print(f"[WARN] No Close data returned for {ticker}, skipping.")
        return None

    if isinstance(close_col, pd.DataFrame):
        if close_col.shape[1] != 1:
            print(f"[WARN] Unexpected Close data shape for {ticker}, skipping.")
            return None
        close_col = close_col.iloc[:, 0]

    close = pd.Series(close_col).dropna()
    if len(close) < RSI_PERIOD + 2:
        print(f"[WARN] Not enough history for {ticker} ({len(close)} rows), skipping.")
        return None

    rsi = compute_rsi(close).dropna()
    if len(rsi) < 2:
        print(f"[WARN] Not enough RSI values for {ticker}, skipping.")
        return None

    prev_rsi = float(rsi.iloc[-2])
    curr_rsi = float(rsi.iloc[-1])
    crossed_up = prev_rsi < RSI_THRESHOLD <= curr_rsi

    return {
        "ticker": ticker,
        "name": TICKERS.get(ticker, ticker),
        "prev_rsi": prev_rsi,
        "curr_rsi": curr_rsi,
        "crossed_up": crossed_up,
        "as_of": close.index[-1].strftime("%Y-%m-%d"),
    }


def display_results(results: list[dict]) -> None:
    crossed = [r for r in results if r["crossed_up"]]
    below_threshold = [r for r in results if r["curr_rsi"] < RSI_THRESHOLD]

    print("=" * 60)
    print(f"RSI({RSI_THRESHOLD}) upward-crossover check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if crossed:
        print(f"\n*** {len(crossed)} stock(s) CROSSED ABOVE RSI {RSI_THRESHOLD} today ***\n")
        for r in crossed:
            print(f"  >> {r['name']} ({r['ticker']}): {r['prev_rsi']:.1f} -> {r['curr_rsi']:.1f}  (as of {r['as_of']})")
    else:
        print(f"\nNo stocks crossed above RSI {RSI_THRESHOLD} today.")

    if below_threshold:
        print(f"\n*** {len(below_threshold)} stock(s) with RSI below {RSI_THRESHOLD} today ***\n")
        for r in sorted(below_threshold, key=lambda x: x["curr_rsi"]):
            print(f"  >> {r['name']} ({r['ticker']}): RSI {r['curr_rsi']:.1f}")
    else:
        print(f"\nNo stocks are below RSI {RSI_THRESHOLD} today.")

    print("\nFull RSI snapshot (all tracked stocks):")
    print("-" * 60)

    table = pd.DataFrame(
        [
            {
                "Ticker": r["ticker"],
                "Name": r["name"],
                "RSI (prev)": round(r["prev_rsi"], 1),
                "RSI (today)": round(r["curr_rsi"], 1),
                "RSI Below 30": "Yes" if r["curr_rsi"] < RSI_THRESHOLD else "No",
                "Crossed?": "YES" if r["crossed_up"] else "No",
            }
            for r in results
        ]
    ).sort_values("RSI (today)")

    print(table.to_string(index=False))
    print("-" * 60)


def main() -> None:
    results = []
    for ticker in TICKERS:
        info = check_ticker(ticker)
        if info is not None:
            results.append(info)

    if not results:
        print("[ERROR] No tickers returned usable data.", file=sys.stderr)
        sys.exit(1)

    display_results(results)


if __name__ == "__main__":
    main()
