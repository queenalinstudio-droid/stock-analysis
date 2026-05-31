// Tiingo daily prices proxy.
// Browser calls: /api/data?ticker=AAPL&startDate=2024-01-01
// Returns:        array of {date, open, high, low, close, volume, ...}

export default async (req) => {
  const url = new URL(req.url);
  const ticker = url.searchParams.get("ticker");
  const startDate = url.searchParams.get("startDate") || "";
  const endDate = url.searchParams.get("endDate") || "";

  if (!ticker) {
    return json({ error: "Missing ticker" }, 400);
  }

  const token = process.env.TIINGO_KEY;
  if (!token) {
    return json({ error: "Server missing TIINGO_KEY env var" }, 500);
  }

  let upstream =
    `https://api.tiingo.com/tiingo/daily/${encodeURIComponent(ticker)}/prices` +
    `?token=${token}`;
  if (startDate) upstream += `&startDate=${encodeURIComponent(startDate)}`;
  if (endDate) upstream += `&endDate=${encodeURIComponent(endDate)}`;

  try {
    const r = await fetch(upstream);
    const body = await r.text();
    return new Response(body, {
      status: r.status,
      headers: {
        "content-type": "application/json",
        "cache-control": "public, max-age=300",
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
