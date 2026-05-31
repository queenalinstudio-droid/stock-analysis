// Tiingo IEX intraday / premarket proxy.
// Browser calls: /api/premarket?ticker=AAPL
// Returns:        array with one object: {last, prevClose, open, high, low, volume, ...}

export default async (req) => {
  const url = new URL(req.url);
  const ticker = url.searchParams.get("ticker");

  if (!ticker) {
    return json({ error: "Missing ticker" }, 400);
  }

  const token = process.env.TIINGO_KEY;
  if (!token) {
    return json({ error: "Server missing TIINGO_KEY env var" }, 500);
  }

  const upstream =
    `https://api.tiingo.com/iex/${encodeURIComponent(ticker)}?token=${token}`;

  try {
    const r = await fetch(upstream);
    const body = await r.text();
    return new Response(body, {
      status: r.status,
      headers: {
        "content-type": "application/json",
        "cache-control": "public, max-age=30",
      },
    });
  } catch (err) {
    return json({ error: String(err) }, 502);
  }
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json" },
  });
}
