from src.database.connection import get_connection


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS daily_quotes (
                symbol TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume REAL, amount REAL, turnover REAL,
                amplitude REAL, change_pct REAL, change_amount REAL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, trade_date)
            );

            CREATE TABLE IF NOT EXISTS stock_profiles (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                industry TEXT,
                market TEXT,
                listing_date TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS watchlist (
                symbol TEXT PRIMARY KEY,
                market TEXT NOT NULL DEFAULT 'A股',
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS financial_cache (
                symbol TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT,
                total REAL NOT NULL,
                technical REAL NOT NULL,
                financial REAL NOT NULL,
                trend REAL NOT NULL,
                risk REAL NOT NULL,
                confidence TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS technical_signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT,
                category TEXT NOT NULL,
                result TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS research_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL DEFAULT 'A股',
                name TEXT,
                trade_date TEXT,
                total_score REAL,
                confidence TEXT,
                report TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS research_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT,
                category TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        for table, column, declaration in (
            ("watchlist", "market", "TEXT NOT NULL DEFAULT 'A股'"),
            ("research_reports", "market", "TEXT NOT NULL DEFAULT 'A股'"),
        ):
            columns = {
                row["name"] for row in conn.execute(f"PRAGMA table_info({table})")
            }
            if column not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
        conn.execute(
            """UPDATE watchlist SET market = 'Crypto'
               WHERE symbol LIKE '%-USD' AND symbol GLOB '*[A-Za-z]*'"""
        )
        conn.execute(
            """UPDATE research_reports SET market = 'Crypto'
               WHERE symbol LIKE '%-USD' AND symbol GLOB '*[A-Za-z]*'"""
        )
        conn.execute(
            """INSERT OR IGNORE INTO watchlist (symbol, market, note, created_at)
               SELECT REPLACE(symbol, '-USD', '-USDT'), market, note, created_at
               FROM watchlist WHERE market = 'Crypto' AND symbol LIKE '%-USD'"""
        )
        conn.execute(
            """DELETE FROM watchlist
               WHERE market = 'Crypto' AND symbol LIKE '%-USD'"""
        )
