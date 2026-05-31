# Personal Trading Tracker — Tape &amp; Tell

A private technical dashboard for your US holdings. Live indicators, plain-language verdicts, P/L tracking. Data from Tiingo. Deploys free on Netlify.

---

## Quick start: Netlify (recommended)

1. **Push this folder to a new GitHub repo.**
2. Go to [netlify.com](https://netlify.com) → sign up with GitHub.
3. **Add new site → Import an existing project → GitHub** → pick this repo.
4. Settings:
   - **Build command:** leave blank
   - **Publish directory:** `.` (a single dot)
   - Click **Deploy**.
5. After the first deploy completes, go to **Site configuration → Environment variables → Add a variable**:
   - Key: `TIINGO_KEY`
   - Value: your Tiingo API key
6. **Deploys → Trigger deploy → Deploy site** so the key takes effect.
7. Click your site URL (`yourname.netlify.app`) — done. HTTPS is on automatically.

**Free tier:** 125,000 function calls/month, 100 GB bandwidth, no credit card, no sleep delay. You'll use a tiny fraction of that.

---

## Local development

1. Copy `secret.py.example` to `secret.py` and paste your real Tiingo key in.
2. Run:
   ```
   python server.py
   ```
3. Open http://localhost:8765/

`secret.py` is gitignored — it never leaves your machine.

---

## Files

- `index.html` — the dashboard (HTML/JS, no build step)
- `server.py` — local dev proxy (Python stdlib only, no pip install)
- `secret.py.example` — template for the local key
- `netlify.toml` — Netlify config + `/api/*` redirects
- `netlify/functions/data.js` — Tiingo daily prices proxy (serverless)
- `netlify/functions/premarket.js` — Tiingo IEX premarket proxy (serverless)
- `.gitignore` — keeps `secret.py` out of GitHub

The serverless functions and `server.py` both speak the same `/api/data` and `/api/premarket` interface, so the exact same `index.html` works locally and on Netlify.

---

## Customizing your portfolio

Open `index.html` and find the `portfolio` array (around line 200). Each entry is:

```javascript
{sym:"NVDA", name:"NVIDIA", shares:61, avgCost:203.867},
```

Edit shares and avgCost to match your broker statement. P/L is computed automatically. To add a ticker on the fly, use the **Add** button in the toolbar — it'll show indicators but P/L will be zero (shares: 0).

---

## Tiingo free tier limits

The free tier gives ~500 API calls per month total. Each page load fetches data for every ticker in your portfolio, so 8 holdings × 30 page loads = 240 calls/month. Comfortable headroom, but don't hammer refresh.

Local mode caches each ticker for 10 minutes; Netlify functions add 5-minute browser cache headers. Both help reduce calls.

---

## Troubleshooting

- **"Server missing TIINGO_KEY"** → set the env var on Netlify (Site configuration → Environment variables) and redeploy.
- **Function returns 404** → make sure `netlify.toml` is at the repo root, not inside a subfolder.
- **"Not enough history" error** → ticker has &lt;30 trading days; pick another.
- **Page is blank** → check the browser console (F12) for errors. Common cause: `netlify.toml` wasn't picked up because the publish directory is wrong (must be `.`).

---

## Disclaimer

This dashboard computes mechanical technical readings — RSI, MACD, moving averages, Bollinger Bands, ATR — and derives suggested entry / target / exit levels from recent swing pivots and volatility. These are not predictions. Markets do what they want. Treat verdicts as one data point, never a substitute for your own judgment, position sizing, or risk management. Nothing here is investment advice.
