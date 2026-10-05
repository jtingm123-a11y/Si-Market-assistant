import re

from src.data_sources.market_data import normalize_symbol


MARKETS = ("A股", "Crypto", "美股")


def normalize_market_symbol(market: str, symbol: str) -> str:
    value = str(symbol).strip().upper()
    if market == "A股":
        return normalize_symbol(value)
    if market == "Crypto":
        if not re.fullmatch(r"[A-Z0-9]{2,15}-USDT", value):
            raise ValueError("请输入有效的 Crypto 代码，例如 BTC-USDT。")
        return value
    if market == "美股":
        if not re.fullmatch(r"(?=.*[A-Z])[A-Z0-9][A-Z0-9.^=-]{0,14}", value):
            raise ValueError("请输入有效的美股代码，例如 AAPL 或 BRK-B。")
        return value
    raise ValueError(f"不支持的市场：{market}")
