"""Yahoo Finance chart data used by the Crypto and US equity research pages."""

from __future__ import annotations

from urllib.parse import quote

import pandas as pd
import requests


def fetch_yahoo_history(symbol: str, period: str = "6mo") -> tuple[pd.DataFrame, dict]:
    safe_symbol = quote(symbol.strip().upper(), safe=".-^=")
    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{safe_symbol}",
        params={"range": period, "interval": "1d"},
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    payload = response.json().get("chart", {})
    if payload.get("error"):
        raise ValueError(str(payload["error"]))
    results = payload.get("result") or []
    if not results:
        raise ValueError(f"行情接口没有返回 {symbol} 的数据。")
    result = results[0]
    quote_data = result.get("indicators", {}).get("quote", [{}])[0]
    frame = pd.DataFrame(quote_data)
    timestamps = result.get("timestamp", [])
    if frame.empty or not timestamps:
        raise ValueError(f"{symbol} 暂无可用的日线数据。")
    frame = frame.reindex(range(len(timestamps)))
    frame["date"] = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None)
    frame = frame.rename(columns={
        "open": "open", "high": "high", "low": "low",
        "close": "close", "volume": "volume",
    })
    for column in ("open", "high", "low", "close", "volume"):
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    if frame.empty:
        raise ValueError(f"{symbol} 的行情数据无有效收盘价。")
    meta = result.get("meta", {})
    close = float(frame.iloc[-1]["close"])
    previous = meta.get("previousClose")
    if previous is None and len(frame) > 1:
        previous = frame.iloc[-2]["close"]
    if previous is None:
        previous = meta.get("chartPreviousClose")
    previous = float(previous) if previous not in (None, 0) else close
    meta["latest_price"] = float(meta.get("regularMarketPrice") or close)
    meta["previous_close"] = previous
    meta["change"] = meta["latest_price"] - previous
    meta["change_pct"] = meta["change"] / previous * 100 if previous else 0.0
    meta["currency"] = meta.get("currency", "USD")
    return frame[["date", "open", "high", "low", "close", "volume"]], meta
