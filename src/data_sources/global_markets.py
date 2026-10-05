from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import requests


MARKETS = (
    ("中国上证指数", "000001.SS"),
    ("中国深证成指", "399001.SZ"),
    ("香港恒生指数", "^HSI"),
    ("美国标普500", "^GSPC"),
    ("美国纳斯达克", "^IXIC"),
    ("日本日经225", "^N225"),
    ("欧洲斯托克50", "^STOXX50E"),
    ("英国富时100", "^FTSE"),
    ("德国DAX", "^GDAXI"),
    ("法国CAC40", "^FCHI"),
    ("韩国综合指数", "^KS11"),
)

CRYPTOS = (
    ("Bitcoin", "BTC-USDT"),
    ("Ethereum", "ETH-USDT"),
    ("Tether", "USDT-USDT"),
    ("BNB", "BNB-USDT"),
    ("XRP", "XRP-USDT"),
    ("Solana", "SOL-USDT"),
    ("USD Coin", "USDC-USDT"),
    ("Dogecoin", "DOGE-USDT"),
    ("TRON", "TRX-USDT"),
    ("Cardano", "ADA-USDT"),
    ("Bitcoin Cash", "BCH-USDT"),
    ("Litecoin", "LTC-USDT"),
    ("Chainlink", "LINK-USDT"),
    ("Polkadot", "DOT-USDT"),
    ("Avalanche", "AVAX-USDT"),
    ("Shiba Inu", "SHIB-USDT"),
    ("Stellar", "XLM-USDT"),
    ("Cosmos", "ATOM-USDT"),
    ("Ethereum Classic", "ETC-USDT"),
    ("NEAR Protocol", "NEAR-USDT"),
)

CRYPTO_CATEGORIES = {
    "BTC-USDT": "价值存储 / PoW",
    "ETH-USDT": "智能合约公链",
    "USDT-USDT": "美元锚定稳定币",
    "BNB-USDT": "交易平台生态代币",
    "XRP-USDT": "支付与跨境结算",
    "SOL-USDT": "高性能智能合约公链",
    "USDC-USDT": "美元锚定稳定币",
    "DOGE-USDT": "Meme 社区代币",
    "TRX-USDT": "智能合约与稳定币结算",
    "ADA-USDT": "权益证明公链",
    "BCH-USDT": "点对点支付 / PoW",
    "LTC-USDT": "支付型 PoW 公链",
    "LINK-USDT": "预言机与数据服务",
    "DOT-USDT": "跨链基础设施",
    "AVAX-USDT": "智能合约公链",
    "SHIB-USDT": "Meme 社区代币",
    "XLM-USDT": "支付与跨境结算",
    "ATOM-USDT": "跨链与权益证明公链",
    "ETC-USDT": "智能合约公链 / PoW",
    "NEAR-USDT": "智能合约公链",
}


def search_crypto_symbols(query: str) -> list[str]:
    """Return supported Crypto symbols matching a name, ticker, or category."""
    normalized_query = query.strip().casefold()
    matches = []
    for name, symbol in CRYPTOS:
        searchable_text = " ".join(
            (name, symbol, symbol.removesuffix("-USDT"), CRYPTO_CATEGORIES[symbol])
        ).casefold()
        if not normalized_query or normalized_query in searchable_text:
            matches.append(symbol)
    return matches


def _fetch_market_quote(item: tuple[str, str]) -> dict:
    name, symbol = item
    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "5d", "interval": "1d"},
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    result = response.json()["chart"]["result"][0]
    meta = result.get("meta", {})
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    valid_closes = [float(value) for value in closes if value is not None]
    price = meta.get("regularMarketPrice")
    previous = meta.get("previousClose")
    if previous is None and len(valid_closes) >= 2:
        previous = valid_closes[-2]
    if previous is None:
        previous = meta.get("chartPreviousClose")
    if price is None and valid_closes:
        price = valid_closes[-1]
    if price is None or previous in (None, 0):
        raise ValueError("行情数据不完整")
    price = float(price)
    previous = float(previous)
    market_timestamp = meta.get("regularMarketTime")
    market_timezone = meta.get("exchangeTimezoneName")
    market_time = "--"
    if market_timestamp is not None:
        try:
            target_timezone = ZoneInfo(market_timezone) if market_timezone else timezone.utc
        except ZoneInfoNotFoundError:
            target_timezone = timezone.utc
        market_time = datetime.fromtimestamp(
            float(market_timestamp), tz=timezone.utc
        ).astimezone(target_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")
    return {
        "市场": name,
        "代码": symbol,
        "最新": price,
        "涨跌": price - previous,
        "涨跌幅": (price - previous) / previous * 100,
        "市场时间": market_time,
    }


def fetch_global_market_quotes() -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_fetch_market_quote, item): item for item in MARKETS}
        for future in as_completed(futures):
            name, _ = futures[future]
            try:
                rows.append(future.result())
            except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                errors.append(f"{name}：{exc}")
    order = {name: index for index, (name, _) in enumerate(MARKETS)}
    quotes = pd.DataFrame(rows)
    if not quotes.empty:
        quotes["_order"] = quotes["市场"].map(order)
        quotes = quotes.sort_values("_order").drop(columns="_order")
    return quotes, errors


def fetch_global_crypto_quotes() -> tuple[pd.DataFrame, list[str]]:
    from src.data_sources.crypto_market_data import fetch_crypto_history
    from src.data_sources.yahoo_market_data import fetch_yahoo_history

    rows: list[dict] = []
    errors: list[str] = []
    try:
        conversion_reference = fetch_yahoo_history("USDT-USD", "5d")
    except Exception as exc:
        return pd.DataFrame(), [f"USDT 汇率：{exc}"]
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fetch_crypto_history, symbol, "5d", conversion_reference): (name, symbol)
            for name, symbol in CRYPTOS
        }
        for future in as_completed(futures):
            name, symbol = futures[future]
            try:
                history, meta = future.result()
                price = float(meta["latest_price"])
                previous = float(meta["previous_close"])
                rows.append({
                    "市场": name,
                    "代码": symbol,
                    "最新": price,
                    "涨跌": price - previous,
                    "涨跌幅": float(meta["change_pct"]),
                    "日线日期（UTC）": pd.to_datetime(
                        history.iloc[-1]["date"], utc=True
                    ).strftime("%Y-%m-%d"),
                })
            except Exception as exc:
                errors.append(f"{name}：{exc}")
    order = {name: index for index, (name, _) in enumerate(CRYPTOS)}
    quotes = pd.DataFrame(rows)
    if not quotes.empty:
        quotes["_order"] = quotes["市场"].map(order)
        quotes = quotes.sort_values("_order").drop(columns="_order")
    return quotes, errors
