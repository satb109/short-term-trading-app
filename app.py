import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, render_template_string, request

from mva_alert import collect_mva_results, format_mva_results

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      nav { margin-bottom: 1rem; }
      nav a { margin-right: 1rem; text-decoration: none; color: #0366d6; }
      button { padding: 0.6rem 1rem; font-size: 1rem; cursor: pointer; }
      pre { background: #f5f5f5; padding: 1rem; white-space: pre-wrap; }
    </style>
  </head>
  <body>
    <h1>Short Term Trading Signals</h1>
    <nav>
      <a href="/">Nifty 50 Signal</a>
      <a href="/nifty-next-50">Nifty Next 50 Signal</a>
      <a href="/30-day-mva-alert">30 Day MVA Signal</a>
    </nav>
    <h2>{{ title }}</h2>
    <form method="post">
      <button type="submit">Run Signal</button>
    </form>
    {% if output %}
      <h2>Result</h2>
      <pre>{{ output }}</pre>
    {% endif %}
  </body>
</html>
"""


def run_report(ticker_set: str, report_type: str = "rsi") -> str:
    repo_dir = Path(__file__).resolve().parent
    if report_type == "mva":
        from mva_alert import NIFTY_100_TICKERS

        results = collect_mva_results(NIFTY_100_TICKERS)
        return format_mva_results(results)

    cmd = [sys.executable, "rsi_alert.py", "--ticker-set", ticker_set]
    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env={**dict(os.environ), "PYTHONPATH": str(repo_dir)},
    )
    return result.stdout or result.stderr or "No output"


@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    if request.method == "POST":
        output = run_report("nifty50")
    return render_template_string(HTML, output=output, title="RSI Alert Nifty 50")


@app.route("/nifty-next-50", methods=["GET", "POST"])
def nifty_next_50():
    output = ""
    if request.method == "POST":
        output = run_report("nifty-next-50")
    return render_template_string(HTML, output=output, title="RSI Alert Nifty Next 50")


@app.route("/30-day-mva-alert", methods=["GET", "POST"])
def thirty_day_mva_alert():
    output = ""
    if request.method == "POST":
        output = run_report("nifty100", report_type="mva")
    return render_template_string(HTML, output=output, title="30 Day MVA Alert")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
