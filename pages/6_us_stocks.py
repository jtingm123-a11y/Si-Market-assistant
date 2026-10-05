import re

import streamlit as st

from src.services.watchlist_service import add_watchlist, list_watchlist
from src.services.market_stock_scanner import render_market_stock_scanner
from src.services.market_chart import create_market_chart
from src.data_sources.yahoo_market_data import fetch_yahoo_history
from src.utils.market_hours import get_us_market_status


US_STOCKS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B",
}
PERIODS = {"1 个月": "1mo", "3 个月": "3mo", "6 个月": "6mo", "1 年": "1y"}


@st.fragment(run_every="30s")
def _render_us_market_clock() -> None:
    current, status = get_us_market_status()
    color = "green" if status == "开盘中" else "blue" if status == "盘前" else "gray"
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        st.badge(status, color=color, icon=":material/schedule:")
        st.caption(f"美东时间 {current:%Y-%m-%d %H:%M:%S}")


title_col, status_col = st.columns([1, 3], vertical_alignment="center")
with title_col:
    st.title("美股研究")
with status_col:
    _render_us_market_clock()
st.caption("状态按美东时间常规工作日交易时段估算；美国节假日可能与实际交易日历不同。")
st.caption("查看热门美股或输入代码查询日线行情。价格单位按交易所返回货币显示。")
render_market_stock_scanner("美股")
with st.form("us_stock_research_form", border=True):
    col_ticker, col_period, col_action = st.columns([3, 2, 1], vertical_alignment="bottom")
    with col_ticker:
        pending_symbol = st.session_state.pop("us_pending_symbol", None)
        pending_selection = next(
            (name for name, ticker in US_STOCKS.items() if ticker == pending_symbol),
            "自定义代码",
        )
        selection_options = ["自定义代码", *US_STOCKS.keys()]
        selection_index = (
            selection_options.index(pending_selection)
            if pending_selection in selection_options else 0
        )
        if pending_symbol and pending_selection == "自定义代码":
            st.session_state["us_custom_symbol"] = pending_symbol
        selection = st.selectbox(
            "热门股票",
            selection_options,
            index=selection_index,
        )
        if selection == "自定义代码":
            custom_symbol = st.text_input(
                "自定义代码", placeholder="例如 NVDA、BRK-B",
                key="us_custom_symbol",
            )
            symbol = custom_symbol.strip().upper()
        else:
            symbol = US_STOCKS[selection]
            st.caption(f"代码：{symbol}")
    with col_period:
        period_label = st.selectbox("历史范围", list(PERIODS), index=2)
    with col_action:
        submitted = st.form_submit_button("查询行情", type="primary")

if submitted:
    if not re.fullmatch(r"[A-Z0-9.^=-]{1,15}", symbol):
        st.error("请输入有效的美股代码（最多 15 位英文字母、数字或 . ^ = -）。")
    else:
        try:
            with st.spinner(f"正在获取 {symbol} 行情..."):
                history, meta = fetch_yahoo_history(symbol, PERIODS[period_label])
            st.session_state["us_stock_research"] = {
                "symbol": symbol, "history": history, "meta": meta,
                "period": period_label,
            }
        except Exception as exc:
            st.error(f"行情获取失败：{exc}")

payload = st.session_state.get("us_stock_research")
if payload:
    history, meta = payload["history"], payload["meta"]
    st.subheader(f"{meta.get('longName') or meta.get('shortName') or payload['symbol']} ({payload['symbol']})")
    watchlist = list_watchlist()
    if "market" in watchlist.columns:
        watchlist = watchlist[watchlist["market"] == "美股"]
    watched_symbols = set(watchlist["symbol"]) if "symbol" in watchlist.columns else set()
    if payload["symbol"] in watched_symbols:
        st.badge("已在自选观察", color="green", icon=":material/bookmark_added:")
    elif st.button(
        "加入自选观察",
        type="secondary",
        icon=":material/bookmark_add:",
        key="add_us_stock_to_watchlist",
    ):
        add_watchlist(payload["symbol"], "来自美股研究", "美股")
        st.success(f"{payload['symbol']} 已加入自选观察。")
    cols = st.columns(4, gap="small")
    currency = meta.get("currency", "USD")
    cols[0].metric("最新价格", f"{currency} {meta['latest_price']:,.2f}")
    cols[1].metric(
        "日涨跌",
        f"{meta['change']:+,.2f}",
        f"{meta['change_pct']:+.2f}%",
        delta_color="inverse",
    )
    cols[2].metric("区间最高", f"{history['high'].max():,.2f}")
    cols[3].metric("区间最低", f"{history['low'].min():,.2f}")

    selected_ma = st.multiselect(
        "均线显示",
        ["MA5", "MA10", "MA20", "MA60"],
        default=["MA5", "MA10", "MA20", "MA60"],
        key="us_stock_selected_ma",
    )
    figure = create_market_chart(
        history,
        selected_ma,
        price_axis_title=f"价格（{currency}）",
        up_color="#34d399",
        down_color="#fb7185",
        skip_weekends=True,
    )
    st.plotly_chart(figure, width="stretch", config={
        "scrollZoom": True, "displaylogo": False, "doubleClick": "reset",
    })
    st.caption("行情由 Yahoo Finance 公开接口提供，可能延迟。分析仅用于研究，不构成投资建议。")
else:
    st.info("选择热门股票或输入代码，点击“查询行情”开始研究。")
