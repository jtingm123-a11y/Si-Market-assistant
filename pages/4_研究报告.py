from pathlib import Path
import logging

import pandas as pd

import streamlit as st

from config.settings import REPORT_EXPORT_DIR
from src.analysis.technical_indicators import add_technical_indicators
from src.data_sources.crypto_market_data import fetch_crypto_history
from src.data_sources.global_markets import CRYPTOS, CRYPTO_CATEGORIES
from src.data_sources.stock_info import fetch_stock_profile
from src.data_sources.yahoo_market_data import fetch_yahoo_history
from src.database.repositories import (
    delete_research_reports, get_research_report, list_research_reports,
    list_watchlist, save_research_report,
)
from src.reports.report_generator import generate_report
from src.services.scoring_service import get_stock_score
from src.services.stock_service import get_analysis
from src.utils.market_symbols import MARKETS, normalize_market_symbol

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_watchlist_name(market: str, symbol: str) -> str:
    if market == "A股":
        return str(fetch_stock_profile(symbol).get("name", "--"))
    history, meta = fetch_yahoo_history(symbol, "5d")
    del history
    return str(meta.get("longName") or meta.get("shortName") or symbol)


st.markdown(
    """<style>
    #MainMenu, header[data-testid="stHeader"], [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    footer {visibility: hidden;}
    [data-testid="stSidebarNav"] {padding-top: 2rem;}
    [data-testid="stSidebarNav"] a {margin: .25rem .6rem; padding: .65rem .8rem;
        border-radius: 10px; font-size: 1.05rem; font-weight: 650;}
    [data-testid="stSidebarNav"] a:hover {background: #1B304B; color: #F1F5F9;}
    [data-testid="stSidebarNav"] a[aria-current="page"] {background: #2B4260; color: #FFFFFF;}
    [data-testid="stSidebarNav"] li:first-child a p {font-size: 0;}
    .report-intro {padding: 1rem 1.2rem; border-radius: 12px; background: #131E2F;
        border: 1px solid #26364D; color: #AFC0D4; margin-bottom: 1rem;}
    .report-area h1 {font-size: 2rem; margin-top: 1rem;}
    .report-area h2 {border-left: 4px solid #60A5FA; padding-left: .7rem; margin-top: 1.5rem;}
    .report-area li {margin: .35rem 0; line-height: 1.6;}
    </style>""",
    unsafe_allow_html=True,
)
st.title("基础分析报告")
st.markdown(
    '<div class="report-intro">选择 A 股、Crypto 或美股生成结构化研究报告；A 股报告含财务评分，其他市场提供技术面与风险观察。</div>',
    unsafe_allow_html=True,
)
market = st.segmented_control(
    "选择市场", MARKETS, default="A股", key="report_market_selector"
)
coin_names = {symbol: name for name, symbol in CRYPTOS}
if market == "Crypto":
    st.info(
        "Crypto 全天候交易（24/7），没有开盘或收盘时段。报告基于公开日线 OHLCV 数据；"
        "技术指标基于日线收盘价变化，不是实时滚动 24 小时收益。"
    )
watchlist = list_watchlist()
market_watchlist = watchlist.loc[watchlist["market"] == market, "symbol"].tolist()
source_options = ["手动输入"] + (["自选观察"] if market_watchlist else [])
symbol_source = st.radio(
    "标的来源",
    source_options,
    horizontal=True,
    key=f"report_symbol_source_{market}",
)
if not market_watchlist:
    st.caption(f"自选观察中暂无{market}标的；先添加标的后即可在此直接选择。")

watchlist_labels = {}
if symbol_source == "自选观察":
    watchlist_names = {}
    name_errors = []
    for symbol in market_watchlist:
        if market == "Crypto":
            watchlist_names[symbol] = coin_names[symbol]
            continue
        try:
            watchlist_names[symbol] = _fetch_watchlist_name(market, symbol)
        except Exception as exc:
            watchlist_names[symbol] = symbol
            name_errors.append(f"{symbol}：{exc}")
    if name_errors:
        st.warning("部分自选标的暂时无法获取名称，仍可按代码选择：\n\n" + "\n".join(name_errors))
    watchlist_labels = {
        symbol: f"{watchlist_names[symbol]}（{symbol}）"
        for symbol in market_watchlist
    }
with st.form("generate_research_report", border=True):
    if symbol_source == "自选观察":
        symbol_input = st.selectbox(
            "选择自选标的",
            market_watchlist,
            format_func=lambda value: watchlist_labels[value],
            key=f"report_watchlist_symbol_{market}",
        )
    elif market == "A股":
        symbol_input = st.text_input(
            "A 股代码", value=st.session_state.get("symbol", ""),
            max_chars=6, placeholder="请输入 6 位 A 股代码",
            key="report_a_symbol",
        )
    elif market == "Crypto":
        symbol_input = st.selectbox(
            "选择币种",
            [symbol for _, symbol in CRYPTOS],
            format_func=lambda value: (
                f"{coin_names[value]} · {CRYPTO_CATEGORIES[value]}（{value}）"
            ),
            key="report_crypto_symbol",
        )
    else:
        symbol_input = st.text_input(
            "美股代码", max_chars=15, placeholder="例如 AAPL、NVDA 或 BRK-B",
            key="report_us_symbol",
        )
    refresh_label = "生成前刷新最新可用日线" if market == "Crypto" else "生成前刷新行情"
    refresh = st.checkbox(refresh_label, value=True)
    submitted = st.form_submit_button("生成报告", type="primary")

retry_payload = st.session_state.pop("report_retry_payload", None)
retry_requested = st.session_state.pop("report_retry", False)
if submitted or retry_requested:
    selected_market = retry_payload["market"] if retry_requested and retry_payload else market
    raw_symbol = retry_payload["symbol"] if retry_requested and retry_payload else symbol_input
    should_refresh = retry_payload["refresh"] if retry_requested and retry_payload else refresh
    try:
        with st.spinner("正在整理数据并生成报告..."):
            symbol = normalize_market_symbol(selected_market, raw_symbol)
            if selected_market == "A股":
                profile, indicators = get_analysis(symbol, refresh=should_refresh)
                score, _, _ = get_stock_score(symbol, indicators, refresh=should_refresh)
                currency = "CNY"
            elif selected_market == "Crypto":
                history, meta = fetch_crypto_history(symbol, "1y")
                indicators = history.rename(columns={"date": "trade_date"})
                indicators["change_pct"] = indicators["close"].pct_change().mul(100)
                indicators["change_amount"] = indicators["close"].diff()
                indicators["amount"] = indicators["close"] * indicators["volume"]
                indicators = add_technical_indicators(indicators)
                profile = {
                    "name": meta.get("longName") or meta.get("shortName") or coin_names[symbol],
                    "industry": "Crypto",
                    "listing_date": "--",
                }
                score = None
                currency = "USDT"
            else:
                history, meta = fetch_yahoo_history(symbol, "1y")
                indicators = history.rename(columns={"date": "trade_date"})
                indicators["change_pct"] = indicators["close"].pct_change().mul(100)
                indicators["change_amount"] = indicators["close"].diff()
                indicators["amount"] = indicators["close"] * indicators["volume"]
                indicators = add_technical_indicators(indicators)
                profile = {
                    "name": meta.get("longName") or meta.get("shortName") or symbol,
                    "industry": selected_market,
                    "listing_date": "--",
                }
                score = None
                currency = meta.get("currency", "USD")
            report = generate_report(
                symbol, profile, indicators, score,
                market=selected_market, currency=currency,
            )
        st.session_state["report"] = report
        st.session_state["report_symbol"] = symbol
        st.session_state["report_market"] = selected_market
        st.session_state["report_id"] = save_research_report(
            symbol, profile.get("name", "--"), indicators.iloc[-1]["trade_date"],
            score, report, market=selected_market,
        )
    except Exception as exc:
        logger.exception(
            "生成%s报告失败：%s", selected_market, raw_symbol,
        )
        message = str(exc)
        if "ProxyError" in message or "Unable to connect to proxy" in message:
            st.error("行情接口暂时无法连接。请检查网络或代理设置后重试。")
            st.info("查询新股票必须联网；网络恢复后重新点击“生成报告”即可。")
        else:
            st.error(f"{selected_market} {raw_symbol} 报告生成失败：{message}")
        st.session_state["report_retry_payload"] = {
            "market": selected_market,
            "symbol": raw_symbol,
            "refresh": should_refresh,
        }
        if st.button("重试生成报告", key="report_retry_button"):
            st.session_state["report_retry"] = True
            st.rerun()

if "report" in st.session_state:
    report = st.session_state["report"]
    st.caption(
        f"当前报告：{st.session_state['report_market']} · "
        f"{st.session_state['report_symbol']}"
    )
    with st.container(border=True):
        st.markdown(report, unsafe_allow_html=True)
    REPORT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{st.session_state['report_symbol']}_report.md"
    st.download_button("下载 Markdown 报告", data=report, file_name=filename, mime="text/markdown")
    if st.button("保存报告到 data/exports"):
        path = Path(REPORT_EXPORT_DIR) / filename
        path.write_text(report, encoding="utf-8")
        st.success(f"已保存：{path}")

st.divider()
st.subheader("历史报告")
history_symbol = st.text_input(
    "按代码筛选（可选）", max_chars=15, key="report_history_symbol",
    placeholder="例如 600519、BTC-USDT 或 AAPL",
)
try:
    normalized_history_symbol = (
        normalize_market_symbol(market, history_symbol) if history_symbol.strip() else None
    )
except ValueError as exc:
    st.warning(str(exc))
    normalized_history_symbol = None
history = list_research_reports(normalized_history_symbol, market=market)
if history.empty:
    st.info(f"暂无{market}历史报告。生成报告后会自动归档。")
else:
    history_display = history.rename(columns={
        "id": "编号", "market": "市场", "symbol": "代码", "name": "名称", "trade_date": "行情日期",
        "total_score": "综合评分", "confidence": "可信度", "created_at": "生成时间",
    })
    st.dataframe(history_display, hide_index=True, width="stretch")
    history_version = st.session_state.get("report_history_version", 0)
    selected_id = st.selectbox(
        "选择历史报告",
        history["id"].tolist(),
        format_func=lambda value: f"报告 #{value}",
        key=f"report_history_selected_{history_version}",
    )
    selected_report = get_research_report(int(selected_id))
    if selected_report:
        st.download_button(
            "下载历史报告",
            data=selected_report["report"],
            file_name=f"{selected_report['symbol']}_report_{selected_report['id']}.md",
            mime="text/markdown",
        )
        with st.expander("查看历史报告内容"):
            st.markdown(selected_report["report"], unsafe_allow_html=True)
    if len(history) >= 2:
        compare_ids = st.multiselect(
            "选择两份报告进行对比", history["id"].tolist(), max_selections=2,
            format_func=lambda value: f"报告 #{value}",
            key=f"report_history_compare_{history_version}",
        )
        if len(compare_ids) == 2:
            compare = history[history["id"].isin(compare_ids)].sort_values("created_at")
            first, second = compare.iloc[0], compare.iloc[1]
            st.subheader("报告评分对比")
            has_scores = pd.notna(first["total_score"]) and pd.notna(second["total_score"])
            st.dataframe(pd.DataFrame({
                "项目": ["综合评分", "行情日期", "可信度"],
                "较早报告": [
                    first["total_score"] if pd.notna(first["total_score"]) else "--",
                    first["trade_date"], first["confidence"] or "--",
                ],
                "较新报告": [
                    second["total_score"] if pd.notna(second["total_score"]) else "--",
                    second["trade_date"], second["confidence"] or "--",
                ],
                "变化": [
                    f"{second['total_score'] - first['total_score']:+.1f}" if has_scores else "--",
                    "--",
                    "--",
                ],
            }), hide_index=True, width="stretch")
    delete_ids = st.multiselect(
        "选择要删除的历史报告（可多选）",
        history["id"].tolist(),
        format_func=lambda value: (
            f"报告 #{value} · "
            f"{history.loc[history['id'] == value, 'symbol'].iloc[0]} · "
            f"{history.loc[history['id'] == value, 'trade_date'].iloc[0]}"
        ),
        key=f"report_history_delete_{history_version}",
    )
    confirm_delete = st.checkbox(
        f"确认永久删除所选的 {len(delete_ids)} 份报告",
        disabled=not delete_ids,
        key=f"confirm_delete_reports_{history_version}",
    )
    if st.button(
        "删除所选报告",
        type="secondary",
        icon=":material/delete:",
        disabled=not delete_ids or not confirm_delete,
        key=f"delete_selected_reports_{history_version}",
    ):
        deleted_count = delete_research_reports([int(report_id) for report_id in delete_ids])
        if deleted_count:
            st.session_state["report_history_version"] = history_version + 1
            st.success(f"已删除 {deleted_count} 份历史报告。")
            st.rerun()
        st.error("所选历史报告不存在或已被删除，请刷新列表后重试。")
