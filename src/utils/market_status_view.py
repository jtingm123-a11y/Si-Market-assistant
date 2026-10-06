from datetime import datetime
from html import escape

import streamlit as st


def render_market_status(status: str, current: datetime, timezone_label: str) -> None:
    if status == "盘中":
        state_class = "is-open"
    elif status in {"盘前", "盘前交易", "集合竞价", "待开盘", "收盘竞价", "盘后交易"}:
        state_class = "is-session"
    else:
        state_class = ""

    st.markdown(
        '<div class="market-clock-card">'
        f'<span class="market-clock-status {state_class}">{escape(status)}</span>'
        f'<span class="market-clock-time">{escape(timezone_label)} · '
        f'{escape(current.strftime("%Y-%m-%d %H:%M:%S"))}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
