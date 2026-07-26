"""30-day moving-average alert report."""

import argparse
import sys
from datetime import datetime

import pandas as pd
import yfinance as yf

from rsi_alert import NIFTY_NEXT_50_TICKERS, TICKERS

NIFTY_100_TICKERS = {**TICKERS, **NIFTY_NEXT_50_TICKERS}
MVA_PERIOD = 30


def check_ticker_mva(ticker: str, ticker_map: dict[str, str] | None = None) -> dict | None:
    data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
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
    if len(close) < MVA_PERIOD + 2:
        print(f"[WARN] Not enough history for {ticker} ({len(close)} rows), skipping.")
        return None

    sma = close.rolling(window=MVA_PERIOD).mean().dropna()
    if len(sma) < 2:
        print(f"[WARN] Not enough MVA values for {ticker}, skipping.")
        return None

    prev_close = float(close.iloc[-2])
    curr_close = float(close.iloc[-1])
    prev_sma = float(sma.iloc[-2])
    curr_sma = float(sma.iloc[-1])
    crossed_up = prev_close <= prev_sma and curr_close > curr_sma

    return {
        "ticker": ticker,
        "name": (ticker_map or TICKERS).get(ticker, ticker),
        "prev_close": prev_close,
        "curr_close": curr_close,
        "prev_mva": prev_sma,
        "curr_mva": curr_sma,
        "crossed_up": crossed_up,
        "as_of": close.index[-1].strftime("%Y-%m-%d"),
    }


def format_mva_results(results: list[dict]) -> str:
    crossed = [r for r in results if r["crossed_up"]]
    lines = []
    lines.append("=" * 60)
    lines.append(f"30-Day MVA upward-cross check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    if crossed:
        lines.append(f"\n*** {len(crossed)} stock(s) crossed above the 30-day moving average today ***\n")
        for r in crossed:
            lines.append(
                f"  >> {r['name']} ({r['ticker']}): {r['prev_close']:.2f} -> {r['curr_close']:.2f} | MVA {r['prev_mva']:.2f} -> {r['curr_mva']:.2f}"
            )
    else:
        lines.append("\nNo stocks crossed above the 30-day moving average today.")

    lines.append("\nFull 30-day MVA snapshot (all tracked stocks):")
    lines.append("-" * 60)

    table = pd.DataFrame(
        [
            {
                "Ticker": r["ticker"],
                "Name": r["name"],
                "Prev Close": round(r["prev_close"], 2),
                "Curr Close": round(r["curr_close"], 2),
                "Prev 30D MVA": round(r["prev_mva"], 2),
                "Curr 30D MVA": round(r["curr_mva"], 2),
                "Crossed Up?": "Yes" if r["crossed_up"] else "No",
            }
            for r in results
        ]
    ).sort_values("Curr Close")

    lines.append(table.to_string(index=False))
    lines.append("-" * 60)
    return "\n".join(lines)


def collect_mva_results(tickers: dict[str, str] | None = None) -> list[dict]:
    results = []
    selected_tickers = tickers or NIFTY_100_TICKERS
    for ticker in selected_tickers:
        info = check_ticker_mva(ticker, selected_tickers)
        if info is not None:
            results.append(info)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker-set", choices=["nifty50", "nifty-next-50", "nifty100"], default="nifty100")
    args = parser.parse_args()

    if args.ticker_set == "nifty50":
        tickers = TICKERS
    elif args.ticker_set == "nifty-next-50":
        tickers = NIFTY_NEXT_50_TICKERS
    else:
        tickers = NIFTY_100_TICKERS

    results = collect_mva_results(tickers)
    if not results:
        print("[ERROR] No tickers returned usable data.", file=sys.stderr)
        sys.exit(1)

    print(format_mva_results(results))


if __name__ == "__main__":
    main()
