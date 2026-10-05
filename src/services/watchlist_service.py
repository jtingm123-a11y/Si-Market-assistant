import pandas as pd

from src.data_sources.crypto_market_data import fetch_crypto_history
from src.data_sources.yahoo_market_data import fetch_yahoo_history
from src.database.repositories import add_watchlist as _add_watchlist
from src.database.repositories import get_watchlist_snapshot, list_watchlist, remove_watchlist
from src.services.stock_service import get_quotes
from src.utils.market_symbols import normalize_market_symbol


def add_watchlist(symbol: str, note: str = "", market: str = "A股") -> None:
    _add_watchlist(normalize_market_symbol(market, symbol), note, market)


def refresh_watchlist(market: str | None = None) -> tuple[list[str], list[str]]:
    """Refresh watchlist quotes and return explicit successes and failures."""
    watchlist = list_watchlist()
    if market:
        watchlist = watchlist[watchlist["market"] == market]
    succeeded, failed = [], []
    for item in watchlist.itertuples(index=False):
        try:
            if item.market == "A股":
                get_quotes(item.symbol, refresh=True)
            elif item.market == "Crypto":
                fetch_crypto_history(item.symbol, "5d")
            else:
                fetch_yahoo_history(item.symbol, "5d")
            succeeded.append(item.symbol)
        except Exception as exc:
            failed.append(f"{item.symbol}：{exc}")
    return succeeded, failed


__all__ = [
    "add_watchlist", "list_watchlist", "remove_watchlist",
    "get_watchlist_snapshot", "refresh_watchlist",
]
