from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis.crypto_opportunities import scan_crypto_opportunities
from src.data_sources.crypto_market_data import fetch_crypto_history
from src.data_sources.global_markets import (
    CRYPTOS, CRYPTO_CATEGORIES, search_crypto_symbols,
)
from src.services.watchlist_service import add_watchlist


COIN_LABELS = {
    symbol: f"{name} · {CRYPTO_CATEGORIES[symbol]} ({symbol})"
    for name, symbol in CRYPTOS
}
PERIODS = {"1 个月": "1mo", "3 个月": "3mo", "6 个月": "6mo", "1 年": "1y"}

st.title("Crypto 研究")
st.info(
    "Crypto 全天候交易（24/7），没有开盘或收盘时段。当前行情来自公开日线数据，"
    "涨跌按接口最新参考价与上一根日线收盘价比较，不等同于实时滚动 24 小时涨跌。"
)
st.caption("主流数字资产行情与日线走势，统一以 USDT 报价。公开 USD 行情按 USDT/USD 汇率换算。")
with st.container(border=True):
    st.subheader("热门与异动扫描")
    st.caption("扫描至少 10 种主流币并按最近日线涨跌和成交量变化排序；日线涨跌绝对值 ≥ 2.5% 或成交量 ≥ 近 5 根日线均量 1.5 倍时标记为异动线索，其余排名靠前者标为活跃度靠前。异动阈值基于日线，不是滚动 24 小时统计。类别是项目用途概览，不代表风险评级或买卖建议。")
    if st.button("扫描热门与异动币种", type="secondary", icon=":material/query_stats:"):
        st.session_state.pop("crypto_opportunities", None)
        try:
            with st.spinner("正在检查主流币日线行情..."):
                candidates, scan_errors = scan_crypto_opportunities()
            st.session_state["crypto_opportunities"] = candidates
            st.session_state["crypto_opportunity_errors"] = scan_errors
            st.session_state["crypto_opportunities_checked_at"] = (
                datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S 北京时间")
            )
        except Exception as exc:
            st.session_state.pop("crypto_opportunity_errors", None)
            st.error(f"扫描失败：{exc}")
    candidates = st.session_state.get("crypto_opportunities")
    if candidates is not None:
        st.caption(
            f"本次扫描到 {len(candidates)} 个币种；价格以 USDT 计；"
            f"本地扫描时间：{st.session_state.get('crypto_opportunities_checked_at', '未知')}。"
        )
        if candidates.empty:
            st.warning("没有成功获取扫描数据，请检查网络后重试。")
        else:
            display_candidates = candidates.rename(columns={
                "name": "名称", "symbol": "代码", "category": "币种类别",
                "latest_price": "最新价格（USDT）",
                "change_pct": "最近日线涨跌幅(%)", "volume_multiple": "成交量/近5根日线均量",
                "status": "扫描结果", "reason": "关注原因",
            })
            st.dataframe(
                display_candidates[[
                    "名称", "代码", "币种类别", "最新价格（USDT）",
                    "最近日线涨跌幅(%)", "成交量/近5根日线均量", "扫描结果", "关注原因",
                ]].style.map(
                    lambda value: "color: #fb7185; font-weight: 650" if value > 0
                    else "color: #34d399; font-weight: 650" if value < 0 else "",
                    subset=["最近日线涨跌幅(%)"],
                ),
                hide_index=True,
                width="stretch",
                column_config={
                    "最新价格（USDT）": st.column_config.NumberColumn(format="%.6f"),
                    "最近日线涨跌幅(%)": st.column_config.NumberColumn(format="%+.2f%%"),
                    "成交量/近5根日线均量": st.column_config.NumberColumn(format="%.2fx"),
                },
            )
            selected_opportunity = st.selectbox(
                "选择币种加入观察池",
                candidates["symbol"].tolist(),
                format_func=lambda value: f"{value} · {candidates.loc[candidates['symbol'] == value, 'reason'].iloc[0]}",
                key="crypto_opportunity_to_watch",
            )
            if st.button("加入自选观察", key="add_crypto_opportunity"):
                add_watchlist(selected_opportunity, "来自热门与异动扫描", "Crypto")
                st.success(f"{selected_opportunity} 已加入自选观察。")
        scan_errors = st.session_state.get("crypto_opportunity_errors", [])
        if scan_errors:
            st.warning("部分币种未能获取行情：\n\n" + "\n".join(scan_errors))

pending_symbol = st.session_state.pop("crypto_pending_symbol", None)
if pending_symbol in COIN_LABELS:
    st.session_state["crypto_research_symbol"] = pending_symbol
search_query = st.text_input(
    "搜索币种",
    placeholder="输入币种名称、代码或类别，例如 Bitcoin、BTC、智能合约",
    key="crypto_symbol_search",
)
coin_symbols = search_crypto_symbols(search_query)
if not coin_symbols:
    st.info("没有找到匹配的币种，请尝试名称、代码或类别关键词。")
elif st.session_state.get("crypto_research_symbol") not in coin_symbols:
    st.session_state["crypto_research_symbol"] = coin_symbols[0]

with st.form("crypto_research_form", border=True):
    col_coin, col_period, col_action = st.columns([3, 2, 1], vertical_alignment="bottom")
    if coin_symbols:
        with col_coin:
            symbol = st.selectbox(
                "选择币种",
                coin_symbols,
                format_func=lambda value: COIN_LABELS[value],
                key="crypto_research_symbol",
            )
    else:
        symbol = None
    with col_period:
        period_label = st.selectbox("历史范围", list(PERIODS), index=2)
    with col_action:
        submitted = st.form_submit_button(
            "查询行情", type="primary", disabled=not coin_symbols
        )

if submitted:
    try:
        with st.spinner("正在获取数字资产行情..."):
            if symbol is None:
                raise ValueError("请先搜索并选择一个币种。")
            history, meta = fetch_crypto_history(symbol, PERIODS[period_label])
        st.session_state["crypto_research"] = {
            "symbol": symbol, "history": history, "meta": meta,
            "period": period_label,
            "fetched_at": datetime.now(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S 北京时间"
            ),
        }
    except Exception as exc:
        st.error(f"行情获取失败：{exc}")

payload = st.session_state.get("crypto_research")
if payload:
    history, meta = payload["history"], payload["meta"]
    st.subheader(COIN_LABELS[payload["symbol"]])
    st.caption(
        f"本地获取时间：{payload['fetched_at']} · 最近日线日期（UTC）："
        f"{pd.to_datetime(history.iloc[-1]['date'], utc=True).strftime('%Y-%m-%d')} · "
        "数据源可能延迟；涨跌为对比上一根日线收盘价，并非滚动 24 小时变化。"
    )
    cols = st.columns(4, gap="small")
    cols[0].metric("最新价格", f"{meta['latest_price']:,.6f} USDT")
    cols[1].metric(
        "最近日线涨跌",
        f"{meta['change']:+,.6f} USDT",
        f"{meta['change_pct']:+.2f}%",
        delta_color="inverse",
        help="接口最新参考价相对前一根日线收盘价的变化，不是实时滚动 24 小时涨跌。",
    )
    cols[2].metric("历史最高", f"{history['high'].max():,.6f} USDT")
    cols[3].metric("历史最低", f"{history['low'].min():,.6f} USDT")

    figure = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=.04, row_heights=[.72, .28])
    figure.add_trace(go.Candlestick(
        x=history["date"], open=history["open"], high=history["high"],
        low=history["low"], close=history["close"], name="日线",
        increasing_line_color="#fb7185", decreasing_line_color="#34d399",
        increasing_fillcolor="#fb7185", decreasing_fillcolor="#34d399",
    ), row=1, col=1)
    figure.add_trace(go.Bar(
        x=history["date"], y=history["volume"], name="成交量",
        marker_color="#38bdf8", opacity=.55,
    ), row=2, col=1)
    figure.update_layout(
        height=650, template="plotly_dark", dragmode="pan",
        hovermode="x unified", margin=dict(l=8, r=8, t=22, b=8),
        xaxis_rangeslider_visible=False,
    )
    figure.update_yaxes(title_text="价格（USDT）", row=1, col=1)
    figure.update_xaxes(rangeslider_visible=False, row=2, col=1)
    st.plotly_chart(figure, width="stretch", config={
        "scrollZoom": True, "displaylogo": False, "doubleClick": "reset",
    })
    st.caption(
        f"报价换算：1 USDT ≈ {meta['usd_per_usdt']:.6f} USD；"
        "Crypto 全天候交易，公开行情可能延迟，不构成投资建议。"
    )
else:
    st.info("选择币种和时间范围，点击“查询行情”开始研究。")
