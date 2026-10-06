from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from src.analysis.crypto_opportunities import scan_crypto_opportunities
from src.analysis.technical_indicators import add_technical_indicators
from src.data_sources.crypto_market_data import convert_usd_crypto_history
from src.data_sources.global_markets import CRYPTOS, search_crypto_symbols
from src.database.repositories import add_watchlist, list_watchlist
from src.reports.report_generator import generate_report
from src.utils.market_hours import get_a_share_market_status, get_us_market_status
from src.utils.market_symbols import normalize_market_symbol


def test_market_symbol_validation_keeps_market_formats_distinct():
    assert normalize_market_symbol("A股", "600519") == "600519"
    assert normalize_market_symbol("Crypto", "btc-usdt") == "BTC-USDT"
    assert normalize_market_symbol("美股", "brk-b") == "BRK-B"
    with pytest.raises(ValueError):
        normalize_market_symbol("Crypto", "AAPL")
    with pytest.raises(ValueError):
        normalize_market_symbol("美股", "600519")


def test_crypto_symbol_search_matches_name_symbol_and_category_case_insensitively():
    assert search_crypto_symbols("bitcoin") == ["BTC-USDT", "BCH-USDT"]
    assert search_crypto_symbols("btc") == ["BTC-USDT"]
    assert search_crypto_symbols("智能合约") == [
        "ETH-USDT", "SOL-USDT", "TRX-USDT", "AVAX-USDT", "ETC-USDT", "NEAR-USDT",
    ]
    assert search_crypto_symbols("not-a-supported-coin") == []


def test_us_stock_can_be_added_to_market_specific_watchlist(tmp_path, monkeypatch):
    import src.database.connection as connection
    from src.database.schema import initialize_database

    monkeypatch.setattr(connection, "DATABASE_PATH", tmp_path / "watchlist.db")
    initialize_database()
    add_watchlist("AAPL", "来自美股研究", "美股")

    watchlist = list_watchlist()
    assert watchlist.iloc[0]["symbol"] == "AAPL"
    assert watchlist.iloc[0]["market"] == "美股"
    assert watchlist.iloc[0]["note"] == "来自美股研究"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-12 09:14", "盘前"),
        ("2026-10-12 09:15", "集合竞价"),
        ("2026-10-12 09:25", "待开盘"),
        ("2026-10-12 09:30", "盘中"),
        ("2026-10-12 11:30", "午间休市"),
        ("2026-10-12 13:00", "盘中"),
        ("2026-10-12 14:57", "收盘竞价"),
        ("2026-10-12 15:00", "已收盘"),
        ("2026-10-06 10:00", "节假日休市"),
        ("2026-10-04 10:00", "周末休市"),
    ],
)
def test_a_share_market_status_tracks_regular_session_boundaries(value, expected):
    local_time = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo("Asia/Shanghai")
    )
    _, status = get_a_share_market_status(local_time)
    assert status == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-05 03:59", "未开市"),
        ("2026-10-05 04:00", "盘前交易"),
        ("2026-10-05 09:29", "盘前交易"),
        ("2026-10-05 09:30", "盘中"),
        ("2026-10-05 15:59", "盘中"),
        ("2026-10-05 16:00", "盘后交易"),
        ("2026-10-05 20:00", "已收盘"),
        ("2026-07-03 10:00", "节假日休市"),
        ("2026-11-27 13:00", "盘后交易"),
        ("2026-10-04 10:00", "周末休市"),
    ],
)
def test_us_market_status_tracks_eastern_session_boundaries(value, expected):
    eastern = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    current, status = get_us_market_status(eastern)
    assert status == expected
    assert current.tzinfo == ZoneInfo("America/New_York")


def test_market_status_requests_calendar_update_outside_supported_dates():
    shanghai_time = datetime(2030, 1, 7, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    new_york_time = datetime(2030, 1, 7, 10, 0, tzinfo=ZoneInfo("America/New_York"))

    assert get_a_share_market_status(shanghai_time)[1] == "交易日历待更新"
    assert get_us_market_status(new_york_time)[1] == "交易日历待更新"


def test_crypto_scanner_returns_explainable_candidates_and_partial_errors(monkeypatch):
    import src.analysis.crypto_opportunities as scanner

    def fake_fetch(symbol, period):
        if symbol == "NEAR-USD":
            raise RuntimeError("接口暂不可用")
        closes = [100, 100, 100, 100, 100, 104] if symbol == "BTC-USD" else [100] * 6
        volumes = [100, 100, 100, 100, 100, 300] if symbol == "BTC-USD" else [100] * 6
        history = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=6),
            "close": closes,
            "open": closes,
            "high": closes,
            "low": closes,
            "volume": volumes,
        })
        return history, {
            "change_pct": 4 if symbol == "BTC-USD" else 0,
            "latest_price": closes[-1],
            "shortName": symbol,
        }

    monkeypatch.setattr(scanner, "fetch_yahoo_history", fake_fetch)
    candidates, errors = scan_crypto_opportunities()

    assert len(candidates) == len(CRYPTOS) - 1
    assert int((candidates["status"] == "活跃度靠前").sum()) >= 9
    bitcoin = candidates.loc[candidates["symbol"] == CRYPTOS[0][1]].iloc[0]
    assert "最近日线涨跌幅上涨 4.00%" in bitcoin["reason"]
    assert "成交量约为近 5 根日线均量的 3.00 倍" in bitcoin["reason"]
    assert bitcoin["category"] == "价值存储 / PoW"
    assert bitcoin["status"] == "异动线索"
    assert len(errors) == 1
    assert "NEAR Protocol" in errors[0]


def test_crypto_history_converts_usd_quotes_using_daily_usdt_usd_rates():
    dates = pd.date_range("2026-01-01", periods=2)
    usd_history = pd.DataFrame({
        "date": dates, "open": [98, 108], "high": [102, 112],
        "low": [97, 107], "close": [100, 110], "volume": [1000, 1200],
    })
    usdt_history = pd.DataFrame({
        "date": dates, "open": [0.98, 0.99], "high": [1.0, 1.01],
        "low": [0.97, 0.98], "close": [0.99, 1.0], "volume": [100, 110],
    })
    converted, meta = convert_usd_crypto_history(
        "BTC-USDT",
        usd_history,
        {"latest_price": 110},
        usdt_history,
        {"latest_price": 1.0},
    )

    assert converted.iloc[0]["close"] == pytest.approx(100 / 0.99)
    assert converted.iloc[1]["close"] == pytest.approx(110)
    assert meta["latest_price"] == pytest.approx(110)
    assert meta["currency"] == "USDT"
    assert meta["usd_per_usdt"] == pytest.approx(1.0)


def test_fetch_crypto_history_loads_usd_pair_and_usdt_conversion(monkeypatch):
    import src.data_sources.crypto_market_data as crypto_data

    dates = pd.date_range("2026-01-01", periods=2)
    base = pd.DataFrame({
        "date": dates, "open": [99, 109], "high": [101, 111],
        "low": [98, 108], "close": [100, 110], "volume": [10, 12],
    })
    rate = pd.DataFrame({
        "date": dates, "open": [0.99, 1], "high": [1, 1.01],
        "low": [0.98, 0.99], "close": [0.99, 1], "volume": [100, 110],
    })
    requests_seen = []

    def fake_fetch(symbol, period):
        requests_seen.append(symbol)
        return (base, {"latest_price": 110}) if symbol == "BTC-USD" else (
            rate, {"latest_price": 1}
        )

    monkeypatch.setattr(crypto_data, "fetch_yahoo_history", fake_fetch)
    history, meta = crypto_data.fetch_crypto_history("BTC-USDT", "1y")

    assert requests_seen == ["BTC-USD", "USDT-USD"]
    assert history.iloc[-1]["close"] == pytest.approx(110)
    assert meta["currency"] == "USDT"


def test_global_crypto_quotes_include_latest_daily_bar_date_utc(monkeypatch):
    import src.data_sources.crypto_market_data as crypto_data
    import src.data_sources.global_markets as global_markets
    import src.data_sources.yahoo_market_data as yahoo_data

    daily_date = pd.Timestamp("2026-05-07")
    history = pd.DataFrame({
        "date": [daily_date], "open": [99], "high": [101],
        "low": [98], "close": [100], "volume": [10],
    })

    def fake_yahoo_history(symbol, period):
        return history, {"latest_price": 1.0}

    def fake_crypto_history(symbol, period, conversion_reference=None):
        return history, {
            "latest_price": 100.0,
            "previous_close": 95.0,
            "change_pct": (100 / 95 - 1) * 100,
        }

    monkeypatch.setattr(yahoo_data, "fetch_yahoo_history", fake_yahoo_history)
    monkeypatch.setattr(crypto_data, "fetch_crypto_history", fake_crypto_history)
    quotes, errors = global_markets.fetch_global_crypto_quotes()

    assert not errors
    assert len(quotes) == len(CRYPTOS)
    assert set(quotes["日线日期（UTC）"]) == {"2026-05-07"}


def test_global_market_quote_exposes_exchange_local_time(monkeypatch):
    import src.data_sources.global_markets as global_markets

    timestamp = datetime(2026, 10, 5, 13, 30, tzinfo=ZoneInfo("UTC")).timestamp()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "chart": {
                    "result": [{
                        "meta": {
                            "regularMarketPrice": 100,
                            "previousClose": 99,
                            "regularMarketTime": timestamp,
                            "exchangeTimezoneName": "America/New_York",
                        },
                        "indicators": {"quote": [{"close": [99]}]},
                    }]
                }
            }

    monkeypatch.setattr(global_markets.requests, "get", lambda *args, **kwargs: FakeResponse())
    quote = global_markets._fetch_market_quote(("美国标普500", "^GSPC"))

    assert quote["市场时间"] == "2026-10-05 09:30:00 EDT"
    assert quote["涨跌幅"] == pytest.approx(100 / 99 * 100 - 100)


def test_non_a_share_report_uses_technical_analysis_without_fake_financial_score():
    dates = pd.date_range("2026-01-01", periods=65, freq="D")
    closes = pd.Series(range(100, 165), dtype=float)
    quotes = pd.DataFrame({
        "trade_date": dates,
        "open": closes - 0.5,
        "high": closes + 1,
        "low": closes - 1,
        "close": closes,
        "volume": 1000,
        "change_pct": closes.pct_change().mul(100),
    })
    indicators = add_technical_indicators(quotes)

    report = generate_report(
        "BTC-USDT",
        {"name": "Bitcoin", "industry": "Crypto", "listing_date": "--"},
        indicators,
        market="Crypto",
        currency="USDT",
    )

    assert "- 市场：Crypto" in report
    assert "- 报价币种：USDT" in report
    assert "日线数据日期（UTC）" in report
    assert "Crypto 全天候交易（24/7）" in report
    assert "相对前一根 UTC 日线收盘价的变化，不是滚动 24 小时收益率" in report
    assert '<span style="color:#F87171;font-weight:700">' in report
    assert "## 三、综合评分" not in report
    assert "不计算综合评分或财务评价" in report
