from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

from src.data_sources.market_screeners import (
    scan_a_share_activity,
    scan_us_stock_activity,
)
from src.services.watchlist_service import add_watchlist


@st.cache_data(ttl=300, max_entries=2, show_spinner=False)
def _load_market_stock_activity(market: str) -> tuple[pd.DataFrame, list[str]]:
    if market == "A股":
        return scan_a_share_activity()
    if market == "美股":
        return scan_us_stock_activity()
    raise ValueError(f"不支持的扫描市场：{market}")


def render_market_stock_scanner(market: str) -> None:
    section_key = "a_share" if market == "A股" else "us_stocks"
    scan_key = f"{section_key}_stock_activity"
    errors_key = f"{scan_key}_errors"
    updated_key = f"{scan_key}_updated_at"
    is_a_share = market == "A股"

    with st.container(border=True):
        st.subheader(f"{market} 热门与异动扫描")
        if is_a_share:
            st.caption(
                "使用新浪财经公开全市场榜单，筛选换手率活跃和成交额靠前的 A 股。"
                "此数据源不提供量比；闭市时行情可能不是当日实时数据。"
            )
        else:
            st.caption(
                "综合美股活跃股榜、涨跌幅榜与成交量对比，关注当前成交量达到 3 个月日均量 "
                "1.5 倍的股票，以及活跃榜和大幅波动个股。行情可能延迟。"
            )

        if st.button(
            f"扫描{market}热门与异动",
            key=f"{scan_key}_button",
            icon=":material/query_stats:",
            type="secondary",
        ):
            _load_market_stock_activity.clear()
            try:
                with st.spinner(f"正在扫描{market}活跃股与成交量异动..."):
                    candidates, errors = _load_market_stock_activity(market)
                st.session_state[scan_key] = candidates
                st.session_state[errors_key] = errors
                st.session_state[updated_key] = datetime.now(
                    ZoneInfo("Asia/Shanghai")
                ).strftime("%Y-%m-%d %H:%M:%S")
            except (
                ImportError,
                requests.RequestException,
                ArithmeticError,
                IndexError,
                KeyError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as exc:
                st.error(f"{market}扫描失败：{exc}")

        candidates = st.session_state.get(scan_key)
        if candidates is None:
            return
        st.caption(
            f"本次扫描 {len(candidates)} 只股票 · "
            f"北京时间 {st.session_state.get(updated_key, '--')}"
        )
        if candidates.empty:
            st.info("当前没有符合筛选条件的股票，或行情源未返回有效结果。")
        else:
            if is_a_share:
                display = candidates.rename(columns={
                    "symbol": "代码",
                    "name": "名称",
                    "price": "最新价",
                    "change_pct": "涨跌幅",
                    "volume_multiple": "量比",
                    "turnover_rate": "换手率",
                    "trade_amount": "成交额（元）",
                    "signal": "信号",
                    "reason": "入选依据",
                })
                display = display[[
                    "代码", "名称", "最新价", "涨跌幅", "换手率",
                    "成交额（元）", "信号", "入选依据",
                ]]
                columns = {
                    "最新价": st.column_config.NumberColumn(
                        format="¥%.2f", alignment="left"
                    ),
                    "涨跌幅": st.column_config.NumberColumn(
                        format="%+.2f%%", alignment="left"
                    ),
                    "换手率": st.column_config.NumberColumn(
                        format="%.2f%%", alignment="left"
                    ),
                    "成交额（元）": st.column_config.NumberColumn(
                        format="¥%.0f", alignment="left"
                    ),
                }
            else:
                display = candidates.rename(columns={
                    "symbol": "代码",
                    "name": "名称",
                    "price": "最新价",
                    "change_pct": "涨跌幅",
                    "volume_multiple": "成交量/3个月日均量",
                    "trade_amount": "当前成交量（股）",
                    "signal": "信号",
                    "reason": "入选依据",
                })
                display = display[[
                    "代码", "名称", "最新价", "涨跌幅",
                    "成交量/3个月日均量", "当前成交量（股）", "信号", "入选依据",
                ]]
                columns = {
                    "最新价": st.column_config.NumberColumn(
                        format="$%.2f", alignment="left"
                    ),
                    "涨跌幅": st.column_config.NumberColumn(
                        format="%+.2f%%", alignment="left"
                    ),
                    "成交量/3个月日均量": st.column_config.NumberColumn(
                        format="%.2fx", alignment="left"
                    ),
                    "当前成交量（股）": st.column_config.NumberColumn(
                        format="%.0f", alignment="left"
                    ),
                }

            st.dataframe(
                display.style.set_properties(**{"text-align": "left"}),
                hide_index=True,
                width="stretch",
                column_config=columns,
            )
            symbols = candidates["symbol"].tolist()
            selection_key = f"{scan_key}_selection"
            if st.session_state.get(selection_key) not in symbols:
                st.session_state[selection_key] = symbols[0]
            symbol_names = candidates.set_index("symbol")["name"].to_dict()
            selected_symbol = st.selectbox(
                "选择股票加入自选",
                symbols,
                format_func=lambda symbol: (
                    f"{symbol} · {symbol_names.get(symbol, '')}".strip(" ·")
                    if is_a_share else symbol
                ),
                key=selection_key,
            )
            if st.button(
                "加入自选",
                key=f"{scan_key}_add",
                icon=":material/bookmark_add:",
            ):
                add_watchlist(selected_symbol, f"来自{market}热门与异动扫描", market)
                st.success(f"{selected_symbol} 已加入自选。")

        errors = st.session_state.get(errors_key, [])
        if errors:
            st.warning("部分榜单暂不可用：" + "；".join(errors))
