from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import pandas as pd
import requests


SCREENER_COLUMNS = [
    "symbol", "name", "price", "change_pct", "volume_multiple",
    "turnover_rate", "trade_amount", "signal", "reason", "attention",
]
US_SCREENER_IDS = ("most_actives", "day_gainers", "day_losers")


def _fetch_sina_a_share_rank(sort_field: str) -> pd.DataFrame:
    session = requests.Session()
    session.trust_env = False
    last_error: requests.RequestException | None = None
    try:
        for attempt in range(2):
            try:
                response = session.get(
                    "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData",
                    params={
                        "page": 1,
                        "num": 100,
                        "sort": sort_field,
                        "asc": 0,
                        "node": "hs_a",
                        "_s_r_a": "init",
                    },
                    timeout=12,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://finance.sina.com.cn/",
                    },
                )
                response.raise_for_status()
                rows = response.json()
                if not isinstance(rows, list):
                    raise ValueError("新浪财经返回了无法识别的 A 股行情数据。")
                return pd.DataFrame(rows)
            except requests.RequestException as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.5)
    finally:
        session.close()
    if last_error is not None:
        raise last_error
    raise RuntimeError("新浪财经行情请求未能完成。")


def scan_a_share_activity() -> tuple[pd.DataFrame, list[str]]:
    """Rank A-shares by turnover ratio and traded value using Sina's public market lists."""
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            amount_future = executor.submit(_fetch_sina_a_share_rank, "amount")
            turnover_future = executor.submit(
                _fetch_sina_a_share_rank, "turnoverratio"
            )
            amount_ranked = amount_future.result()
            turnover_ranked = turnover_future.result()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(
            "无法连接新浪财经公开行情接口。请检查网络连接或防火墙设置后重试；"
            "扫描会绕过系统代理并自动重试一次。"
        ) from exc

    required = {
        "code", "name", "trade", "changepercent", "amount", "turnoverratio",
    }
    for label, ranked in (("成交额", amount_ranked), ("换手率", turnover_ranked)):
        if ranked.empty:
            raise ValueError(f"新浪财经未返回按{label}排序的 A 股行情。")
        missing = required.difference(ranked.columns)
        if missing:
            raise ValueError(
                f"新浪财经 A 股行情缺少字段：{', '.join(sorted(missing))}"
            )

    amount_ranked = amount_ranked.copy()
    turnover_ranked = turnover_ranked.copy()
    amount_ranked["amount_rank"] = range(1, len(amount_ranked) + 1)
    turnover_ranked["turnover_rank"] = range(1, len(turnover_ranked) + 1)
    frame = pd.concat(
        [amount_ranked, turnover_ranked], ignore_index=True
    ).drop_duplicates("code", keep="first")
    amount_rank_map = amount_ranked.set_index("code")["amount_rank"]
    turnover_rank_map = turnover_ranked.set_index("code")["turnover_rank"]
    frame["amount_rank"] = frame["code"].map(amount_rank_map)
    frame["turnover_rank"] = frame["code"].map(turnover_rank_map)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame["turnoverratio"] = pd.to_numeric(frame["turnoverratio"], errors="coerce")
    frame["trade"] = pd.to_numeric(frame["trade"], errors="coerce")
    frame["changepercent"] = pd.to_numeric(frame["changepercent"], errors="coerce")
    frame = frame.dropna(subset=["amount", "trade"]).copy()
    frame = frame.loc[
        (frame["amount_rank"] <= 30) | (frame["turnover_rank"] <= 30)
    ].copy()
    def describe_activity(row: pd.Series) -> tuple[str, str]:
        signals = []
        reasons = []
        if pd.notna(row["turnover_rank"]) and row["turnover_rank"] <= 30:
            signals.append("换手率活跃")
            reasons.append(f"全市场换手率排名第 {int(row['turnover_rank'])}")
        if pd.notna(row["amount_rank"]) and row["amount_rank"] <= 30:
            signals.append("成交额靠前")
            reasons.append(f"全市场成交额排名第 {int(row['amount_rank'])}")
        return "、".join(signals), "；".join(reasons)

    activity = frame.apply(describe_activity, axis=1)
    frame["signal"] = activity.str[0]
    frame["reason"] = activity.str[1]
    frame["attention"] = (
        (31 - frame["turnover_rank"].fillna(31).clip(upper=31))
        + (31 - frame["amount_rank"].fillna(31).clip(upper=31))
    )
    frame["symbol"] = frame["code"].astype(str).str.zfill(6)
    frame["price"] = frame["trade"]
    frame["change_pct"] = frame["changepercent"]
    frame["volume_multiple"] = None
    frame["turnover_rate"] = frame["turnoverratio"]
    frame["trade_amount"] = frame["amount"]
    frame["name"] = frame["name"].astype(str)
    frame = frame.sort_values(
        ["attention", "trade_amount"], ascending=False
    ).head(30)
    return frame[[
        "symbol", "name", "price", "change_pct", "volume_multiple",
        "turnover_rate", "trade_amount", "signal", "reason", "attention",
    ]].reset_index(drop=True), []


def _fetch_yahoo_screener(screener_id: str) -> list[dict]:
    response = requests.get(
        "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved",
        params={
            "formatted": "false",
            "scrIds": screener_id,
            "count": 50,
        },
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("finance", {}).get("result") or []
    if not results or not isinstance(results[0].get("quotes"), list):
        raise ValueError(f"Yahoo Finance 未返回 {screener_id} 股票列表。")
    return results[0]["quotes"]


def scan_us_stock_activity() -> tuple[pd.DataFrame, list[str]]:
    """Combine Yahoo most-active and price-mover lists with volume comparisons."""
    quotes_by_symbol: dict[str, dict] = {}
    source_errors: list[str] = []
    with ThreadPoolExecutor(max_workers=len(US_SCREENER_IDS)) as executor:
        futures = {
            executor.submit(_fetch_yahoo_screener, screener_id): screener_id
            for screener_id in US_SCREENER_IDS
        }
        for future in as_completed(futures):
            screener_id = futures[future]
            try:
                quotes = future.result()
            except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                source_errors.append(f"{screener_id}：{exc}")
                continue
            for rank, quote in enumerate(quotes, start=1):
                symbol = quote.get("symbol")
                if not isinstance(symbol, str) or not symbol:
                    continue
                current = quotes_by_symbol.setdefault(symbol, {
                    "symbol": symbol,
                    "name": quote.get("shortName") or quote.get("longName") or symbol,
                    "price": quote.get("regularMarketPrice"),
                    "change_pct": quote.get("regularMarketChangePercent"),
                    "volume": quote.get("regularMarketVolume"),
                    "average_volume": quote.get("averageDailyVolume3Month"),
                    "active_rank": None,
                    "mover": False,
                })
                if screener_id == "most_actives":
                    current["active_rank"] = rank
                else:
                    current["mover"] = True

    rows = []
    for quote in quotes_by_symbol.values():
        volume = pd.to_numeric(quote["volume"], errors="coerce")
        average_volume = pd.to_numeric(quote["average_volume"], errors="coerce")
        price = pd.to_numeric(quote["price"], errors="coerce")
        change_pct = pd.to_numeric(quote["change_pct"], errors="coerce")
        volume_multiple = (
            float(volume / average_volume)
            if pd.notna(volume) and pd.notna(average_volume) and average_volume > 0
            else None
        )
        is_anomaly = volume_multiple is not None and volume_multiple >= 1.5
        is_active = quote["active_rank"] is not None
        is_price_mover = (
            quote["mover"] and pd.notna(change_pct) and abs(float(change_pct)) >= 5
        )
        if not (is_anomaly or is_active or is_price_mover):
            continue
        signals = []
        reasons = []
        if is_anomaly:
            signals.append("成交量异动")
            reasons.append(f"当前成交量为 3 个月日均量的 {volume_multiple:.2f} 倍")
        if is_active:
            signals.append("成交活跃")
            reasons.append(f"进入 Yahoo Finance 活跃股榜第 {quote['active_rank']} 位")
        if is_price_mover:
            signals.append("涨跌幅靠前")
            reasons.append(f"当日涨跌幅 {float(change_pct):+.2f}%")
        attention = (
            (volume_multiple or 0) * 10
            + (51 - quote["active_rank"] if is_active else 0)
            + (abs(float(change_pct)) / 10 if pd.notna(change_pct) else 0)
        )
        rows.append({
            "symbol": quote["symbol"],
            "name": quote["name"],
            "price": float(price) if pd.notna(price) else None,
            "change_pct": float(change_pct) if pd.notna(change_pct) else None,
            "volume_multiple": volume_multiple,
            "turnover_rate": None,
            "trade_amount": float(volume) if pd.notna(volume) else None,
            "signal": "、".join(signals),
            "reason": "；".join(reasons),
            "attention": attention,
        })

    rows.sort(key=lambda item: item["attention"], reverse=True)
    return pd.DataFrame(rows[:30], columns=SCREENER_COLUMNS), source_errors
