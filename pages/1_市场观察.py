from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_sources.global_markets import fetch_global_crypto_quotes, fetch_global_market_quotes


st.markdown(
    """<style>
    .market-hero {position:relative; overflow:hidden; padding:1.65rem 1.8rem; margin-bottom:1.1rem;
        border:1px solid rgba(96,165,250,.2); border-radius:20px;
        background:radial-gradient(ellipse at 88% 8%,rgba(56,189,248,.16),transparent 33%),
        linear-gradient(120deg,#14253d,#111827 62%,#17263a);
        box-shadow:0 16px 38px rgba(2,8,23,.16);}
    .market-hero:after {content:""; position:absolute; top:-95px; right:-65px; width:310px; height:250px;
        border:1px solid rgba(103,232,249,.1); border-radius:50%;
        background:radial-gradient(ellipse at center,rgba(34,211,238,.13),rgba(59,130,246,.045) 44%,transparent 70%);
        filter:blur(2px); pointer-events:none; animation:hero-glow 9s ease-in-out infinite;}
    .market-hero > * {position:relative; z-index:1;}
    .market-eyebrow {display:inline-flex; align-items:center; gap:.5rem; color:#93c5fd;
        font-size:.7rem; font-weight:750; letter-spacing:.16em;}
    .market-eyebrow:before {content:""; width:7px; height:7px; border-radius:50%; background:#60a5fa;
        box-shadow:0 0 12px rgba(96,165,250,.75);}
    .market-hero h1 {margin:.55rem 0 .35rem; font-size:2.05rem; letter-spacing:-.04em;}
    .market-hero p {margin:0; color:#a7b8cc; font-size:.95rem;}
    .market-note {color:#94a3b8; font-size:.82rem;}
    @media (max-width:720px) {
        .market-hero {padding:1.45rem 1.25rem; margin-bottom:1.4rem; border-radius:17px;}
        .market-hero h1 {font-size:1.8rem; line-height:1.25;}
        .market-hero p {max-width:32rem; font-size:.93rem; line-height:1.7;}
        .market-eyebrow {font-size:.68rem;}
    }
    </style>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="market-hero"><div class="market-eyebrow">GLOBAL MARKETS</div>'
    '<h1>市场总览</h1><p>全球主要指数与主流数字资产，一屏掌握跨市场变化。</p></div>',
    unsafe_allow_html=True,
)


def _format_quote_price(value: float) -> str:
    if abs(value) < 0.01:
        return f"{value:,.8f}".rstrip("0").rstrip(".")
    if abs(value) < 1:
        return f"{value:,.6f}".rstrip("0").rstrip(".")
    return f"{value:,.2f}"


refresh_col, time_col = st.columns([1, 4], vertical_alignment="center")
with refresh_col:
    refresh = st.button("刷新数据", type="primary", icon=":material/refresh:")

if refresh:
    with st.spinner("正在并发获取全球指数与 Crypto 数据..."):
        index_quotes, index_errors = fetch_global_market_quotes()
        crypto_quotes, crypto_errors = fetch_global_crypto_quotes()
    st.session_state["market_index_quotes"] = index_quotes
    st.session_state["market_index_errors"] = index_errors
    st.session_state["market_crypto_quotes"] = crypto_quotes
    st.session_state["market_crypto_errors"] = crypto_errors
    st.session_state["all_markets_updated_at"] = datetime.now(
        ZoneInfo("Asia/Shanghai")
    ).strftime("%Y-%m-%d %H:%M:%S")

with time_col:
    updated_at = st.session_state.get("all_markets_updated_at")
    st.caption(f"本次刷新时间（北京时间）：{updated_at or '尚未刷新'} · 数据可能延迟")

indices = st.session_state.get("market_index_quotes")
cryptos = st.session_state.get("market_crypto_quotes")
tab_indices, tab_crypto = st.tabs(["全球指数", "Crypto 主流币"])


def _render_quotes(
    frame: pd.DataFrame | None, errors: list[str], unit: str, is_crypto: bool = False,
) -> None:
    if frame is None:
        st.info("点击“刷新数据”获取最新市场总览。")
        return
    if frame.empty:
        st.warning("暂时没有获取到行情。请稍后刷新，或检查网络连接。")
    else:
        latest_column = f"最新（{unit}）" if unit else "最新"
        change_column = f"日线涨跌（{unit}）" if is_crypto else (
            f"涨跌（{unit}）" if unit else "涨跌"
        )
        change_pct_column = "最近日线涨跌幅 (%)" if is_crypto else "涨跌幅 (%)"
        metric_cols = st.columns(min(4, len(frame)), gap="small")
        for column, (_, row) in zip(metric_cols, frame.head(4).iterrows()):
            change_pct = float(row["涨跌幅"])
            with column:
                st.metric(
                    str(row["市场"]),
                    f"{_format_quote_price(float(row['最新']))} {unit}".strip(),
                    f"{change_pct:+.2f}%",
                    delta_color="inverse",
                    border=True,
                )
        chart_frame = frame.sort_values("涨跌幅").copy()
        chart_frame["百分比标签"] = chart_frame["涨跌幅"].map(lambda value: f"{value:+.2f}%")
        chart_frame["标签颜色"] = chart_frame["涨跌幅"].map(
            lambda value: "#fb7185" if value > 0 else "#34d399" if value < 0 else "#cbd5e1"
        )
        chart = px.bar(
            chart_frame,
            x="涨跌幅",
            y="市场",
            orientation="h",
            color="涨跌幅",
            color_continuous_scale=["#34d399", "#26364b", "#fb7185"],
            color_continuous_midpoint=0,
            text="百分比标签",
            labels={"涨跌幅": change_pct_column, "市场": ""},
            template="plotly_dark",
        )
        chart.update_traces(
            textposition="outside",
            textfont_color=chart_frame["标签颜色"].tolist(),
            cliponaxis=False,
        )
        chart.update_layout(
            height=max(260, len(frame) * 34),
            margin=dict(l=8, r=54, t=18, b=8),
            coloraxis_showscale=False,
            showlegend=False,
        )
        extent = max(abs(float(frame["涨跌幅"].min())), abs(float(frame["涨跌幅"].max())))
        padding = max(extent * .22, .25)
        chart.update_xaxes(
            zeroline=True,
            zerolinecolor="#64748b",
            ticksuffix="%",
            range=[float(frame["涨跌幅"].min()) - padding, float(frame["涨跌幅"].max()) + padding],
        )
        st.plotly_chart(chart, width="stretch", config={"displaylogo": False})
        display = frame.rename(columns={
            "市场": "资产", "代码": "代码", "最新": latest_column,
            "涨跌": change_column, "涨跌幅": change_pct_column,
            "日线日期（UTC）": "最近日线日期（UTC）",
            "市场时间": "交易所当地时间",
        }).copy()
        numeric_columns = [latest_column, change_column, change_pct_column]
        for column in numeric_columns:
            if column in display:
                display[column] = pd.to_numeric(display[column], errors="coerce")
        if unit:
            for column in (latest_column, change_column):
                if column not in display:
                    continue
                display[column] = display[column].map(
                    lambda value: _format_quote_price(float(value))
                    if pd.notna(value) else "--"
                )
        format_config = {
            change_column: "{:+,.2f}",
            change_pct_column: "{:+.2f}%",
        }
        if not unit:
            format_config[latest_column] = "{:,.2f}"
        if unit:
            format_config.pop(change_column, None)
        column_config = {
            latest_column: st.column_config.NumberColumn(
                latest_column, format="%.2f", alignment="left"
            ),
            change_pct_column: st.column_config.NumberColumn(
                change_pct_column, format="%+.2f%%", alignment="left"
            ),
        }
        if unit:
            column_config[latest_column] = st.column_config.TextColumn(
                latest_column, alignment="left"
            )
            column_config[change_column] = st.column_config.TextColumn(
                change_column, alignment="left"
            )
        else:
            column_config[change_column] = st.column_config.NumberColumn(
                change_column, format="%+,.2f", alignment="left"
            )
        st.dataframe(
            display.style.format(format_config).map(
                lambda value: "color: #fb7185; font-weight: 650" if value > 0
                else "color: #34d399; font-weight: 650" if value < 0 else "",
                subset=[change_pct_column],
            ).set_properties(**{"text-align": "left"}),
            hide_index=True,
            width="stretch",
            column_config=column_config,
        )
    if errors:
        st.warning("部分市场数据暂不可用：" + "；".join(errors))


with tab_indices:
    st.caption("涵盖中国、香港、美国、欧洲、日本和韩国代表性指数；表格按接口可用性标注各交易所当地行情时间。")
    _render_quotes(indices, st.session_state.get("market_index_errors", []), "")

with tab_crypto:
    st.info(
        "Crypto 全天候交易（24/7），没有开盘或收盘时段。此处展示公开接口的最近日线及"
        "相对前一根日线的涨跌，不是实时滚动 24 小时涨跌；点击“刷新数据”手动获取，数据可能延迟。"
    )
    st.caption(
        "覆盖 BTC、ETH、USDT、BNB、XRP、SOL 等主流币种；报价单位为 USDT，"
        "表中标注最近日线日期（UTC）。"
    )
    _render_quotes(
        cryptos, st.session_state.get("market_crypto_errors", []),
        "USDT", is_crypto=True,
    )

st.caption("行情通过 Yahoo Finance 公开接口获取，可能延迟或暂时不可用，仅供研究参考。")
