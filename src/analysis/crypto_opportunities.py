from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from src.data_sources.crypto_market_data import convert_usd_crypto_history
from src.data_sources.global_markets import CRYPTOS, CRYPTO_CATEGORIES
from src.data_sources.yahoo_market_data import fetch_yahoo_history


def _scan_coin(
    name: str,
    symbol: str,
    usdt_history: pd.DataFrame,
    usdt_meta: dict,
) -> dict:
    usd_history, usd_meta = fetch_yahoo_history(
        f"{symbol.removesuffix('-USDT')}-USD", "1mo"
    )
    history, meta = convert_usd_crypto_history(
        symbol, usd_history, usd_meta, usdt_history, usdt_meta
    )
    closes = pd.to_numeric(history["close"], errors="coerce").dropna()
    if len(closes) < 2:
        raise ValueError("可用日线不足，无法判断近期异动。")

    change_pct = float(meta["change_pct"])
    volumes = pd.to_numeric(history["volume"], errors="coerce").dropna()
    volume_multiple = None
    if len(volumes) >= 6 and volumes.iloc[-6:-1].mean() > 0:
        volume_multiple = float(volumes.iloc[-1] / volumes.iloc[-6:-1].mean())

    price_move = abs(change_pct) >= 2.5
    volume_surge = volume_multiple is not None and volume_multiple >= 1.5
    reasons = []
    if price_move:
        direction = "上涨" if change_pct > 0 else "下跌"
        reasons.append(f"最近日线涨跌幅{direction} {abs(change_pct):.2f}%")
    if volume_surge and volume_multiple is not None:
        reasons.append(f"成交量约为近 5 根日线均量的 {volume_multiple:.2f} 倍")
    attention = abs(change_pct) * 0.7 + max((volume_multiple or 1) - 1, 0) * 2
    return {
        "name": meta.get("longName") or meta.get("shortName") or name,
        "symbol": symbol,
        "category": CRYPTO_CATEGORIES[symbol],
        "latest_price": float(meta.get("latest_price", closes.iloc[-1])),
        "change_pct": change_pct,
        "volume_multiple": volume_multiple,
        "attention": attention,
        "status": "异动线索" if price_move or volume_surge else "常规观察",
        "reason": "；".join(reasons) if reasons else "未触发涨跌或成交量异动阈值",
    }


def scan_crypto_opportunities() -> tuple[pd.DataFrame, list[str]]:
    candidates: list[dict] = []
    errors: list[str] = []
    usdt_history, usdt_meta = fetch_yahoo_history("USDT-USD", "1mo")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_scan_coin, name, symbol, usdt_history, usdt_meta): (name, symbol)
            for name, symbol in CRYPTOS
        }
        for future in as_completed(futures):
            name, _ = futures[future]
            try:
                candidates.append(future.result())
            except Exception as exc:
                errors.append(f"{name}：{exc}")
    candidates.sort(key=lambda item: item["attention"], reverse=True)
    for rank, candidate in enumerate(candidates):
        if candidate["status"] == "常规观察" and rank < 10:
            candidate["status"] = "活跃度靠前"
    return pd.DataFrame(candidates), errors
