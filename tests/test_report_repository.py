import pandas as pd

from src.database.repositories import (
    delete_research_report,
    delete_research_reports,
    get_research_report,
    list_research_reports,
    save_research_report,
)
from src.database.schema import initialize_database


def test_research_report_round_trip(tmp_path, monkeypatch):
    import src.database.connection as connection

    monkeypatch.setattr(connection, "DATABASE_PATH", tmp_path / "reports.db")
    initialize_database()
    score = {"total": 72.5, "confidence": "高"}
    report_id = save_research_report("600519", "测试", pd.Timestamp("2024-01-02"), score, "# 报告")
    assert get_research_report(report_id)["report"] == "# 报告"
    assert list_research_reports("600519").iloc[0]["total_score"] == 72.5


def test_research_reports_store_market_and_allow_unscored_assets(tmp_path, monkeypatch):
    import src.database.connection as connection

    monkeypatch.setattr(connection, "DATABASE_PATH", tmp_path / "markets.db")
    initialize_database()
    report_id = save_research_report(
        "BTC-USDT", "Bitcoin", pd.Timestamp("2024-01-02"), None,
        "# Crypto report", market="Crypto",
    )

    assert get_research_report(report_id)["market"] == "Crypto"
    history = list_research_reports(market="Crypto")
    assert history.iloc[0]["symbol"] == "BTC-USDT"
    assert pd.isna(history.iloc[0]["total_score"])
    assert list_research_reports(market="A股").empty


def test_delete_research_report_removes_only_the_selected_report(tmp_path, monkeypatch):
    import src.database.connection as connection

    monkeypatch.setattr(connection, "DATABASE_PATH", tmp_path / "delete-report.db")
    initialize_database()
    deleted_id = save_research_report(
        "600519", "Test", pd.Timestamp("2024-01-02"), None, "# Delete me"
    )
    kept_id = save_research_report(
        "000001", "Keep", pd.Timestamp("2024-01-02"), None, "# Keep me"
    )

    assert delete_research_report(deleted_id)
    assert get_research_report(deleted_id) is None
    assert get_research_report(kept_id)["report"] == "# Keep me"
    assert not delete_research_report(deleted_id)


def test_delete_multiple_research_reports_keeps_unselected_reports(tmp_path, monkeypatch):
    import src.database.connection as connection

    monkeypatch.setattr(connection, "DATABASE_PATH", tmp_path / "delete-multiple.db")
    initialize_database()
    deleted_ids = [
        save_research_report(
            f"60000{index}", f"Delete {index}", pd.Timestamp("2024-01-02"),
            None, f"# Report {index}",
        )
        for index in range(2)
    ]
    kept_id = save_research_report(
        "000001", "Keep", pd.Timestamp("2024-01-02"), None, "# Keep me"
    )

    assert delete_research_reports(deleted_ids + [deleted_ids[0]]) == 2
    assert all(get_research_report(report_id) is None for report_id in deleted_ids)
    assert get_research_report(kept_id)["report"] == "# Keep me"
    assert delete_research_reports([]) == 0


def test_schema_migrates_existing_market_tables(tmp_path, monkeypatch):
    import sqlite3
    import src.database.connection as connection

    database = tmp_path / "legacy.db"
    monkeypatch.setattr(connection, "DATABASE_PATH", database)
    with sqlite3.connect(database) as conn:
        conn.executescript(
            """
            CREATE TABLE watchlist (
                symbol TEXT PRIMARY KEY, note TEXT, created_at TEXT
            );
            CREATE TABLE research_reports (
                id INTEGER PRIMARY KEY, symbol TEXT, name TEXT, trade_date TEXT,
                total_score REAL, confidence TEXT, report TEXT, created_at TEXT
            );
            INSERT INTO watchlist(symbol, note) VALUES ('600519', '');
            INSERT INTO watchlist(symbol, note) VALUES ('BTC-USD', 'legacy crypto');
            INSERT INTO research_reports(symbol, report)
            VALUES ('BTC-USD', '# old crypto report');
            """
        )

    initialize_database()

    with sqlite3.connect(database) as conn:
        watchlist_market = conn.execute(
            "SELECT market FROM watchlist WHERE symbol = '600519'"
        ).fetchone()[0]
        crypto_symbols = [
            row[0] for row in conn.execute(
                "SELECT symbol FROM watchlist WHERE market = 'Crypto'"
            )
        ]
        report_columns = {row[1] for row in conn.execute("PRAGMA table_info(research_reports)")}
        crypto_report_market = conn.execute(
            "SELECT market FROM research_reports WHERE symbol = 'BTC-USD'"
        ).fetchone()[0]
    assert watchlist_market == "A股"
    assert "market" in report_columns
    assert crypto_symbols == ["BTC-USDT"]
    assert crypto_report_market == "Crypto"
