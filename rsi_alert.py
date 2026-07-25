"""
RSI(20) Upward-Crossover Alert
------------------------------
Checks a fixed list of NSE-listed stocks daily and emails you the ones whose
14-period RSI has just crossed UP through 20 (i.e. yesterday's RSI was below
20 and today's RSI is at/above 20 - a classic "exiting oversold" signal).

Designed to be run once per weekday by GitHub Actions (see rsi_alert.yml),
but it will also run fine locally: `python rsi_alert.py`.

Required environment variables (set as GitHub Secrets in production):
    GMAIL_ADDRESS       - the Gmail address the alert is sent FROM
    GMAIL_APP_PASSWORD  - a 16-character Gmail App Password (not your login password)
    RECIPIENT_EMAIL     - the address to send the alert TO (can be the same Gmail address)
"""

import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# NSE ticker -> display name. yfinance needs the ".NS" suffix for NSE stocks.
TICKERS = {
    "TITAN.NS": "Titan Company",
    "NH.NS": "Narayana Hrudayalaya",
    "BAJAJHLDNG.NS": "Bajaj Holdings & Investment",
    "BAJFINANCE.NS": "Bajaj Finance",
    "RELIANCE.NS": "Reliance Industries",
    "LT.NS": "Larsen & Toubro",
    "APOLLOHOSP.NS": "Apollo Hospitals Enterprise",
    "ABB.NS": "ABB India",
    "HAL.NS": "Hindustan Aeronautics",
    "BSE.NS": "BSE Limited",
}

RSI_PERIOD = 14
RSI_THRESHOLD = 20

# If True, you get an email every run (even "no crossovers today").
# If False, you only get emailed when at least one stock actually crosses.
ALWAYS_SEND_EMAIL = False


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

    if data.empty or "Close" not in data:
        print(f"[WARN] No data returned for {ticker}, skipping.")
        return None

    close = data["Close"].dropna()
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
        "prev_rsi": prev_rsi,
        "curr_rsi": curr_rsi,
        "crossed_up": crossed_up,
        "as_of": close.index[-1].strftime("%Y-%m-%d"),
    }


def build_email_body(results: list[dict], crossed: list[dict]) -> str:
    lines = []
    lines.append(f"RSI(20) upward-crossover check - {datetime.now().strftime('%Y-%m-%d %H:%M')} IST")
    lines.append("")

    if crossed:
        lines.append(f"{len(crossed)} stock(s) crossed ABOVE RSI 20 today:")
        lines.append("")
        for r in crossed:
            name = TICKERS.get(r["ticker"], r["ticker"])
            lines.append(
                f"  - {name} ({r['ticker']}): RSI {r['prev_rsi']:.1f} -> {r['curr_rsi']:.1f} "
                f"(as of {r['as_of']})"
            )
        lines.append("")
    else:
        lines.append("No stocks crossed above RSI 20 today.")
        lines.append("")

    lines.append("Full RSI snapshot (all tracked stocks):")
    for r in results:
        name = TICKERS.get(r["ticker"], r["ticker"])
        flag = " <-- CROSSED" if r["crossed_up"] else ""
        lines.append(f"  - {name} ({r['ticker']}): RSI {r['curr_rsi']:.1f}{flag}")

    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())

    print("Email sent.")


def main() -> None:
    results = []
    for ticker in TICKERS:
        info = check_ticker(ticker)
        if info is not None:
            results.append(info)

    crossed = [r for r in results if r["crossed_up"]]

    # Always print a log to the GitHub Actions console, regardless of email settings.
    print(build_email_body(results, crossed))

    if not results:
        print("[ERROR] No tickers returned usable data - not sending email.", file=sys.stderr)
        sys.exit(1)

    if crossed or ALWAYS_SEND_EMAIL:
        subject = (
            f"RSI Alert: {len(crossed)} stock(s) crossed above 20"
            if crossed
            else "RSI check: no crossovers today"
        )
        send_email(subject, build_email_body(results, crossed))
    else:
        print("No crossovers and ALWAYS_SEND_EMAIL is False - no email sent.")


if __name__ == "__main__":
    main()
