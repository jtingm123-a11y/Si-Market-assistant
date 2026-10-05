import pandas as pd

from src.data_sources.yahoo_market_data import fetch_yahoo_history


class _Response:
    def raise_for_status(self):
        return None

    @staticmethod
    def json():
        return {
            "chart": {
                "error": None,
                "result": [{
                    "timestamp": [1725148800, 1725235200],
                    "indicators": {"quote": [{
                        "open": [100, 105], "high": [110, 115],
                        "low": [95, 101], "close": [105, 110],
                        "volume": [1000, 1200],
                    }]},
                    "meta": {
                        "currency": "USD", "regularMarketPrice": 110,
                        "chartPreviousClose": 90, "symbol": "TEST",
                    },
                }],
            },
        }


def test_fetch_yahoo_history_parses_candles_and_quote_meta(monkeypatch):
    import src.data_sources.yahoo_market_data as market_data

    monkeypatch.setattr(market_data.requests, "get", lambda *args, **kwargs: _Response())
    history, meta = fetch_yahoo_history("TEST", "1mo")
    assert len(history) == 2
    assert list(history.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert meta["change"] == 5
    assert meta["change_pct"] > 0
