import pandas as pd
import streamlit as st

from src.data_sources.global_markets import CRYPTOS, CRYPTO_CATEGORIES
from src.data_sources.crypto_market_data import fetch_crypto_history
from src.data_sources.stock_info import fetch_stock_profile
from src.data_sources.yahoo_market_data import fetch_yahoo_history
from src.database.repositories import get_watchlist_snapshot
from src.services.watchlist_service import (
    add_watchlist, list_watchlist, refresh_watchlist, remove_watchlist,
)
from src.utils.market_symbols import MARKETS, normalize_market_symbol


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_stock_name(symbol: str) -> str:
    return fetch_stock_profile(symbol).get("name", "--")


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_external_snapshot(market: str, symbol: str) -> dict:
    if market == "Crypto":
        history, meta = fetch_crypto_history(symbol, "5d")
        date_column = "date"
    else:
        history, meta = fetch_yahoo_history(symbol, "5d")
        date_column = "date"
    latest = history.iloc[-1]
    return {
        "trade_date": latest[date_column],
        "close": meta["latest_price"],
        "change_pct": meta["change_pct"],
        "volume": latest["volume"],
        "amount": None,
        "updated_at": pd.Timestamp.now(tz="Asia/Shanghai"),
        "name": meta.get("longName") or meta.get("shortName") or symbol,
    }


def _color_change(value: object) -> str:
    number = pd.to_numeric(str(value).replace("%", ""), errors="coerce")
    if pd.isna(number) or number == 0:
        return ""
    return "color: #F87171; font-weight: 700" if number > 0 else "color: #34D399; font-weight: 700"


st.title("自选观察")
st.caption("统一跟踪 A 股、Crypto 和美股；行情来自本地缓存或公开行情接口。")

if st.button("查看我的观察池", type="secondary", key="show_watchlist_button"):
    st.session_state["watchlist_visible"] = True
    st.rerun()

market = st.selectbox("添加市场", MARKETS, key="watchlist_add_market")
with st.form("add_watchlist_form", border=True):
    if market == "A股":
        symbol = st.text_input("A 股代码", max_chars=6, placeholder="例如 600519")
    elif market == "Crypto":
        symbol = st.selectbox(
            "选择币种",
            [code for _, code in CRYPTOS],
            format_func=lambda code: (
                f"{dict((ticker, name) for name, ticker in CRYPTOS)[code]} · "
                f"{CRYPTO_CATEGORIES[code]}（{code}）"
            ),
        )
    else:
        symbol = st.text_input("美股代码", max_chars=15, placeholder="例如 AAPL、NVDA 或 BRK-B")
    note = st.text_input("备注（可选）", placeholder="例如：长期关注、等待信号")
    submitted = st.form_submit_button("加入观察池", type="primary")

if submitted:
    try:
        normalized_symbol = normalize_market_symbol(market, symbol)
        add_watchlist(normalized_symbol, note.strip(), market)
        st.success(f"{normalized_symbol} 已加入自选观察。")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

all_watchlist = list_watchlist()
refresh_message = st.session_state.pop("watchlist_refresh_message", None)
if refresh_message:
    st.success(refresh_message["success"])
    if refresh_message["failed"]:
        st.warning("以下标的刷新失败：\n\n" + "\n".join(refresh_message["failed"]))

if not st.session_state.get("watchlist_visible", False):
    st.caption("添加标的后，点击“查看我的观察池”查看行情并进行管理。")
else:
    watchlist_market = st.segmented_control(
        "观察市场", MARKETS, default="A股", key="watchlist_market_filter",
    )
    watchlist = all_watchlist[all_watchlist["market"] == watchlist_market]
    st.subheader(f"{watchlist_market}观察池")
    if watchlist_market == "Crypto":
        st.info(
            "Crypto 全天候交易（24/7），不会收盘或休市。此处涨跌以接口最新参考价比较上一根日线收盘价，"
            "不是实时滚动 24 小时涨跌；行情通过公开接口获取并缓存 5 分钟，可手动刷新。"
        )
    if watchlist.empty:
        st.info(f"观察池中还没有{watchlist_market}标的。")
    else:
        failed_quotes = []
        if watchlist_market == "A股":
            snapshot = get_watchlist_snapshot()
            snapshot = snapshot[snapshot["market"] == watchlist_market].copy()
            names = {}
            for code in snapshot["symbol"]:
                try:
                    names[code] = _fetch_stock_name(code)
                except Exception as exc:
                    names[code] = "--"
                    failed_quotes.append(f"{code}名称：{exc}")
            snapshot["name"] = snapshot["symbol"].map(names).fillna("--")
        else:
            rows = []
            for item in watchlist.itertuples(index=False):
                try:
                    quote = _fetch_external_snapshot(watchlist_market, item.symbol)
                except Exception as exc:
                    quote = {
                        "trade_date": None, "close": None, "change_pct": None,
                        "volume": None, "amount": None, "updated_at": None,
                        "name": item.symbol,
                    }
                    failed_quotes.append(f"{item.symbol}：{exc}")
                rows.append({
                    "symbol": item.symbol,
                    "market": item.market,
                    "note": item.note,
                    "created_at": item.created_at,
                    **quote,
                })
            snapshot = pd.DataFrame(rows)
        if failed_quotes:
            st.warning("部分行情或名称暂不可用：\n\n" + "\n".join(failed_quotes))

        cached_count = int(snapshot["trade_date"].notna().sum())
        changes = pd.to_numeric(snapshot["change_pct"], errors="coerce")
        average_change = changes.mean()
        rising_count = int((changes > 0).sum())
        falling_count = int((changes < 0).sum())
        flat_count = int((changes == 0).sum())
        summary_columns = st.columns(3, gap="small")
        summary_columns[0].metric("观察标的", f"{len(watchlist)} 个", border=True)
        summary_columns[1].metric(
            "已有日线" if watchlist_market == "Crypto" else "已有行情",
            f"{cached_count} 个",
            border=True,
        )
        average_text = "--" if pd.isna(average_change) else f"{average_change:+.2f}%"
        summary_label = "平均日线涨跌" if watchlist_market == "Crypto" else "观察池平均涨跌"
        if pd.isna(average_change):
            summary_columns[2].metric(summary_label, "--", border=True)
        else:
            summary_columns[2].metric(
                summary_label, " ",
                delta=average_text, delta_color="inverse", border=True,
            )
        st.caption(f"上涨 {rising_count} · 下跌 {falling_count} · 平盘 {flat_count}")

        if st.button("刷新当前市场行情", type="primary"):
            with st.spinner(f"正在刷新{watchlist_market}观察池行情..."):
                succeeded, failed = refresh_watchlist(watchlist_market)
            _fetch_external_snapshot.clear()
            st.session_state["watchlist_refresh_message"] = {
                "success": f"已成功刷新 {len(succeeded)} 个标的。"
                if succeeded else "本次没有标的刷新成功。",
                "failed": failed,
            }
            st.rerun()

        sort_by = st.selectbox(
            "排序方式", ["添加时间", "涨跌幅（高到低）", "涨跌幅（低到高）", "代码"],
        )
        if sort_by == "涨跌幅（高到低）":
            snapshot = snapshot.assign(
                _sort=pd.to_numeric(snapshot["change_pct"], errors="coerce")
            ).sort_values("_sort", ascending=False, na_position="last")
        elif sort_by == "涨跌幅（低到高）":
            snapshot = snapshot.assign(
                _sort=pd.to_numeric(snapshot["change_pct"], errors="coerce")
            ).sort_values("_sort", na_position="last")
        elif sort_by == "代码":
            snapshot = snapshot.sort_values("symbol")

        st.dataframe(
            snapshot.rename(columns={
                "market": "市场", "symbol": "代码", "name": "名称",
                "note": "备注",
                "trade_date": "最近日线日期（UTC）" if watchlist_market == "Crypto" else "行情日期",
                "close": "最新参考价（USDT）" if watchlist_market == "Crypto" else "最新价",
                "change_pct": "日线涨跌幅(%)" if watchlist_market == "Crypto" else "涨跌幅(%)",
                "volume": "成交量", "amount": "成交额",
                "updated_at": "本地获取时间" if watchlist_market == "Crypto" else "行情更新时间",
            }).assign(
                **{
                    (
                        "日线涨跌幅(%)" if watchlist_market == "Crypto" else "涨跌幅(%)"
                    ): lambda frame: pd.to_numeric(
                        frame[
                            "日线涨跌幅(%)" if watchlist_market == "Crypto" else "涨跌幅(%)"
                        ],
                        errors="coerce",
                    ).map(lambda value: "--" if pd.isna(value) else f"{value:+.2f}%")
                }
            ).style.map(
                _color_change,
                subset=["日线涨跌幅(%)" if watchlist_market == "Crypto" else "涨跌幅(%)"],
            ),
            width="stretch",
            hide_index=True,
        )

        research_symbol = st.selectbox(
            "选择标的进行研究",
            snapshot["symbol"].tolist(),
            format_func=lambda code: (
                f"{code}（{snapshot.loc[snapshot['symbol'] == code, 'name'].iloc[0]}）"
            ),
        )
        if st.button("研究所选标的", type="secondary", key="watchlist_research_button"):
            if watchlist_market == "A股":
                st.session_state["symbol"] = research_symbol
                st.session_state["auto_research"] = True
                st.switch_page("pages/2_个股研究.py")
            elif watchlist_market == "Crypto":
                st.session_state["crypto_pending_symbol"] = research_symbol
                st.switch_page("pages/5_crypto.py")
            else:
                st.session_state["us_pending_symbol"] = research_symbol
                st.switch_page("pages/6_us_stocks.py")

        remove_symbol = st.selectbox(
            "选择要移除的代码", watchlist["symbol"].tolist(), key="watchlist_remove_symbol",
        )
        if st.button("从观察池移除"):
            remove_watchlist(remove_symbol)
            st.rerun()
