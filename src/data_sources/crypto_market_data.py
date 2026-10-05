"""Crypto OHLCV data quoted in USDT, converted from Yahoo USD pairs."""

from __future__ import annotations

import pandas as pd

from src.data_sources.yahoo_market_data import fetch_yahoo_history


def convert_usd_crypto_history(
    symbol: str,
    history: pd.DataFrame,
    meta: dict,
    usdt_history: pd.DataFrame,
    usdt_meta: dict,
) -> tuple[pd.DataFrame, dict]:
    if history.empty or usdt_history.empty:
        raise ValueError(f"{symbol} 缺少行情或 USDT 汇率数据，无法换算报价。")

    crypto = history.copy()
    crypto_dates = pd.to_datetime(crypto["date"]).dt.normalize()
    rates = usdt_history.assign(
        date=pd.to_datetime(usdt_history["date"]).dt.normalize()
    ).set_index("date")["close"]
    aligned_rates = rates.reindex(crypto_dates).ffill()
    if aligned_rates.isna().any() or (aligned_rates <= 0).any():
        raise ValueError("USDT/USD 汇率数据不完整或无效，无法换算报价。")

    for column in ("open", "high", "low", "close"):
        crypto[column] = pd.to_numeric(crypto[column], errors="coerce") / aligned_rates.to_numpy()

    converted_meta = dict(meta)
    latest_rate = float(usdt_meta.get("latest_price") or rates.iloc[-1])
    if latest_rate <= 0:
        raise ValueError("USDT/USD 汇率必须大于零。")
    latest_usdt = float(meta.get("latest_price") or history.iloc[-1]["close"]) / latest_rate
    converted_meta["latest_price"] = latest_usdt
    converted_meta["previous_close"] = float(crypto.iloc[-2]["close"]) if len(crypto) > 1 else float(crypto.iloc[-1]["close"])
    converted_meta["change"] = latest_usdt - converted_meta["previous_close"]
    converted_meta["change_pct"] = (
        converted_meta["change"] / converted_meta["previous_close"] * 100
        if converted_meta["previous_close"] else 0.0
    )
    converted_meta["currency"] = "USDT"
    converted_meta["usd_per_usdt"] = latest_rate
    converted_meta["quote_symbol"] = symbol
    return crypto, converted_meta


def fetch_crypto_history(
    symbol: str,
    period: str = "6mo",
    conversion_reference: tuple[pd.DataFrame, dict] | None = None,
) -> tuple[pd.DataFrame, dict]:
    normalized = symbol.strip().upper()
    if not normalized.endswith("-USDT"):
        raise ValueError("Crypto 行情代码须采用 USDT 报价，例如 BTC-USDT。")
    asset = normalized[:-5]
    if not asset:
        raise ValueError("Crypto 代码不能为空。")

    usd_history, usd_meta = fetch_yahoo_history(f"{asset}-USD", period)
    if conversion_reference is not None:
        usdt_history, usdt_meta = conversion_reference
    elif asset == "USDT":
        usdt_history, usdt_meta = usd_history, usd_meta
    else:
        usdt_history, usdt_meta = fetch_yahoo_history("USDT-USD", period)
    return convert_usd_crypto_history(
        normalized, usd_history, usd_meta, usdt_history, usdt_meta
    )
