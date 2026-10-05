import pandas as pd
import pytest
import requests

from src.data_sources.market_screeners import (
    scan_a_share_activity,
    scan_us_stock_activity,
)


def test_a_share_scanner_combines_turnover_and_traded_value_rankings(monkeypatch):
    import src.data_sources.market_screeners as screeners

    amount_ranked = pd.DataFrame([
        {"code": "600001", "name": "High Amount", "trade": "10", "changepercent": 2,
         "amount": 8_000_000, "turnoverratio": 1.0},
        {"code": "600002", "name": "Both Rankings", "trade": "20", "changepercent": -1,
         "amount": 6_000_000, "turnoverratio": 9.0},
        {"code": "600003", "name": "Other", "trade": "30", "changepercent": 0.2,
         "amount": 500_000, "turnoverratio": 0.5},
    ])
    turnover_ranked = pd.DataFrame([
        {"code": "600002", "name": "Both Rankings", "trade": "20", "changepercent": -1,
         "amount": 6_000_000, "turnoverratio": 9.0},
        {"code": "600004", "name": "High Turnover", "trade": "40", "changepercent": 0.5,
         "amount": 2_000_000, "turnoverratio": 7.0},
    ])
    monkeypatch.setattr(
        screeners,
        "_fetch_sina_a_share_rank",
        lambda sort: amount_ranked if sort == "amount" else turnover_ranked,
    )

    candidates, errors = scan_a_share_activity()

    assert not errors
    assert set(candidates["symbol"]) == {
        "600001", "600002", "600003", "600004",
    }
    both = candidates.loc[candidates["symbol"] == "600002"].iloc[0]
    assert both["signal"] == "换手率活跃、成交额靠前"
    assert "换手率排名第 1" in both["reason"]
    assert "成交额排名第 2" in both["reason"]
    other = candidates.loc[candidates["symbol"] == "600003"].iloc[0]
    assert other["signal"] == "成交额靠前"


def test_sina_a_share_request_bypasses_proxy_and_retries(monkeypatch):
    import src.data_sources.market_screeners as screeners

    class Response:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return [{"code": "600001"}]

    class Session:
        def __init__(self):
            self.trust_env = True
            self.calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise requests.ConnectionError("temporary network interruption")
            return Response()

        @staticmethod
        def close():
            return None

    sessions = []

    def create_session():
        session = Session()
        sessions.append(session)
        return session

    monkeypatch.setattr(screeners.requests, "Session", create_session)
    monkeypatch.setattr(screeners.time, "sleep", lambda _: None)

    result = screeners._fetch_sina_a_share_rank("amount")

    assert sessions[0].trust_env is False
    assert sessions[0].calls == 2
    assert result.iloc[0]["code"] == "600001"


def test_a_share_scanner_reports_actionable_error_when_network_is_unavailable(monkeypatch):
    import src.data_sources.market_screeners as screeners

    def fail_fetch(_sort_field):
        raise requests.ConnectionError("proxy details")

    monkeypatch.setattr(screeners, "_fetch_sina_a_share_rank", fail_fetch)

    with pytest.raises(RuntimeError, match="检查网络连接或防火墙设置"):
        scan_a_share_activity()


def test_us_stock_scanner_combines_activity_volume_and_large_moves(monkeypatch):
    import src.data_sources.market_screeners as screeners

    data = {
        "most_actives": [
            {
                "symbol": "AAA",
                "shortName": "Active Co",
                "regularMarketPrice": 12.5,
                "regularMarketVolume": 3_000_000,
                "averageDailyVolume3Month": 1_000_000,
                "regularMarketChangePercent": 2.0,
            },
        ],
        "day_gainers": [
            {
                "symbol": "BBB",
                "shortName": "Mover Co",
                "regularMarketPrice": 24,
                "regularMarketVolume": 500_000,
                "averageDailyVolume3Month": 1_000_000,
                "regularMarketChangePercent": 8.0,
            },
            {
                "symbol": "AAA",
                "shortName": "Active Co",
                "regularMarketPrice": 12.5,
                "regularMarketVolume": 3_000_000,
                "averageDailyVolume3Month": 1_000_000,
                "regularMarketChangePercent": 2.0,
            },
        ],
        "day_losers": [],
    }
    monkeypatch.setattr(
        screeners,
        "_fetch_yahoo_screener",
        lambda screener_id: data[screener_id],
    )

    candidates, errors = scan_us_stock_activity()

    assert not errors
    assert list(candidates["symbol"]) == ["AAA", "BBB"]
    active = candidates.loc[candidates["symbol"] == "AAA"].iloc[0]
    mover = candidates.loc[candidates["symbol"] == "BBB"].iloc[0]
    assert set(active["signal"].split("、")) == {"成交量异动", "成交活跃"}
    assert "3.00 倍" in active["reason"]
    assert "涨跌幅靠前" in mover["signal"]
    assert "8.00%" in mover["reason"]
