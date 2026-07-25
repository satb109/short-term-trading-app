# RSI 20 Crossover Check

Checks 10 NSE stocks and **prints to the console** which ones have a 14-period
RSI that just crossed **up through 20** (moved from below 20 to at/above 20).

No email, no secrets, no credentials needed - just run the script.

## Tracked stocks

| NSE Ticker | Company |
|---|---|
| TITAN.NS | Titan Company |
| NH.NS | Narayana Hrudayalaya |
| BAJAJHLDNG.NS | Bajaj Holdings & Investment |
| BAJFINANCE.NS | Bajaj Finance |
| RELIANCE.NS | Reliance Industries |
| LT.NS | Larsen & Toubro |
| APOLLOHOSP.NS | Apollo Hospitals Enterprise |
| ABB.NS | ABB India |
| HAL.NS | Hindustan Aeronautics |
| BSE.NS | BSE Limited |

To change the list, edit the `TICKERS` dictionary at the top of `rsi_alert.py`.

## Running it locally

```bash
pip install -r requirements.txt
python rsi_alert.py
```

You'll see something like:

```
============================================================
RSI(20) upward-crossover check - 2026-07-25 19:00
============================================================

*** 2 stock(s) CROSSED ABOVE RSI 20 today ***

  >> Titan Company (TITAN.NS): 15.2 -> 24.7  (as of 2026-07-24)
  >> Hindustan Aeronautics (HAL.NS): 18.9 -> 22.1  (as of 2026-07-24)

Full RSI snapshot (all tracked stocks):
------------------------------------------------------------
     Ticker                  Name  RSI (prev)  RSI (today) Crossed?
     HAL.NS Hindustan Aeronautics        18.9         22.1      YES
   TITAN.NS         Titan Company        15.2         24.7      YES
RELIANCE.NS   Reliance Industries        45.0         47.3
------------------------------------------------------------
```

## Running it on a schedule (GitHub Actions) - important caveat

The included `.github/workflows/rsi_alert.yml` will still run the script
automatically Monday-Friday at 7:00 PM IST. **But** GitHub Actions has no
"screen" of its own - the printed output lands in that run's log, which you
have to open manually:

1. Repo -> **Actions** tab -> click the run -> click the job -> expand the
   "Run RSI check" step.

It will **not** proactively notify you the way the email version did - you'd
need to go check. If you mainly want a hands-off daily nudge, the previous
email-based version is better suited to that; this console version is best
for:
- running on your own machine/terminal whenever you want a quick check, or
- occasionally glancing at the Actions log if you don't mind checking manually.

### Setting up the GitHub Actions version
1. Create a repo and upload `rsi_alert.py`, `requirements.txt`, and
   `.github/workflows/rsi_alert.yml` (keep the folder structure).
2. No secrets to configure this time - there's nothing to authenticate.
3. Actions tab -> "RSI 20 Crossover Check" -> **Run workflow** to test it,
   then check the log as described above.

## Notes

- Data comes from Yahoo Finance via the `yfinance` library - free, generally
  reliable for NSE data, but not an official/paid feed. Treat this as a
  personal screening tool, not a trading system.
- RSI uses Wilder's smoothing (the standard/original method), 14-period.
