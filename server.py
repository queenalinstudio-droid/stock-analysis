#!/usr/bin/env python3
"""
Tape & Tell — local data server.

Serves index.html and proxies Tiingo so your API key never reaches the browser.
This is for LOCAL DEVELOPMENT only. On Netlify, the equivalent serverless
functions in `netlify/functions/` handle the same job.

Run:
    python server.py

Then open http://localhost:8765/

The Tiingo key is loaded from (in order):
    1. environment variable TIINGO_KEY
    2. secret.py file in this folder (TIINGO_KEY = "...")
"""
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("PORT", 8765))
HERE = Path(__file__).parent.resolve()

# Try env var first, then secret.py
TIINGO_KEY = os.environ.get("TIINGO_KEY")
if not TIINGO_KEY:
    try:
        from secret import TIINGO_KEY  # noqa: F401
    except ImportError:
        TIINGO_KEY = None

# Simple in-memory cache so refreshes don't burn API calls
CACHE = {}  # (kind, sym) -> (timestamp, body_bytes)
CACHE_TTL = {"data": 600, "premarket": 30}  # seconds


def fetch_tiingo(kind: str, ticker: str, query: dict) -> bytes:
    """Fetch from Tiingo. Raises HTTPError on failure."""
    if kind == "data":
        params = {"token": TIINGO_KEY}
        for k in ("startDate", "endDate"):
            if query.get(k):
                params[k] = query[k][0]
        url = (
            f"https://api.tiingo.com/tiingo/daily/{urllib.parse.quote(ticker)}/prices"
            f"?{urllib.parse.urlencode(params)}"
        )
    elif kind == "premarket":
        params = {"token": TIINGO_KEY}
        url = (
            f"https://api.tiingo.com/iex/{urllib.parse.quote(ticker)}"
            f"?{urllib.parse.urlencode(params)}"
        )
    else:
        raise ValueError(f"unknown kind: {kind}")

    req = urllib.request.Request(url, headers={
        "User-Agent": "tape-and-tell/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}", flush=True)

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, json.dumps({"error": msg}).encode("utf-8"))

    def _api(self, kind, parsed):
        if not TIINGO_KEY:
            return self._err(500, "Server missing TIINGO_KEY (set env var or secret.py)")
        query = urllib.parse.parse_qs(parsed.query)
        ticker = (query.get("ticker", [""])[0] or "").strip().upper()
        if not ticker:
            return self._err(400, "Missing 'ticker' query param")

        now = time.time()
        key = (kind, ticker, parsed.query)
        cached = CACHE.get(key)
        if cached and (now - cached[0] < CACHE_TTL[kind]):
            return self._send(200, cached[1])

        try:
            body = fetch_tiingo(kind, ticker, query)
            CACHE[key] = (now, body)
            self._send(200, body)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            self._err(e.code, f"Tiingo HTTP {e.code}: {detail}")
        except Exception as e:
            self._err(502, f"Fetch failed: {e}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/data":
            return self._api("data", parsed)
        if path == "/api/premarket":
            return self._api("premarket", parsed)

        # Serve static files
        if path in ("/", ""):
            return self._serve_file("index.html", "text/html; charset=utf-8")
        name = path.lstrip("/")
        if "/" in name or ".." in name:
            return self._err(404, "not found")
        target = HERE / name
        if target.is_file():
            ct = "text/html; charset=utf-8" if name.endswith(".html") else "text/plain; charset=utf-8"
            return self._serve_file(name, ct)
        return self._err(404, "not found")

    def _serve_file(self, name, ctype):
        target = HERE / name
        if not target.is_file():
            return self._err(404, "not found")
        self._send(200, target.read_bytes(), ctype)


def main():
    if not TIINGO_KEY:
        print("⚠️  Warning: TIINGO_KEY not set. API calls will fail.")
        print("    Either:  set TIINGO_KEY environment variable")
        print("    Or:      create secret.py with TIINGO_KEY = \"your_key_here\"")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("─" * 60)
    print("  Tape & Tell server running")
    print(f"  → Open  http://localhost:{PORT}/  in your browser")
    print("  → Stop  Ctrl+C")
    print("─" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Bye.")
        server.shutdown()


if __name__ == "__main__":
    main()
