from flask import Flask, render_template_string, request
import subprocess
import sys
from pathlib import Path

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>RSI Alert Runner</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      button { padding: 0.6rem 1rem; font-size: 1rem; cursor: pointer; }
      pre { background: #f5f5f5; padding: 1rem; white-space: pre-wrap; }
    </style>
  </head>
  <body>
    <h1>RSI Alert</h1>
    <form method="post">
      <button type="submit">Run RSI Script</button>
    </form>
    {% if output %}
      <h2>Result</h2>
      <pre>{{ output }}</pre>
    {% endif %}
  </body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    if request.method == "POST":
        repo_dir = Path(__file__).resolve().parent
        result = subprocess.run(
            [sys.executable, "rsi_alert.py"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(repo_dir)},
        )
        output = result.stdout or result.stderr or "No output"
    return render_template_string(HTML, output=output)


if __name__ == "__main__":
    port = int(__import__("os").environ.get("PORT", "5001"))
    app.run(debug=True, host="0.0.0.0", port=port)
