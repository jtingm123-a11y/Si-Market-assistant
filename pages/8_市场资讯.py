from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.data_sources.market_news import (
    NEWS_CATEGORIES,
    NEWS_PROVIDERS,
    fetch_market_news,
)


st.markdown(
    """<style>
    .news-hero {padding:1.45rem 1.6rem; margin-bottom:1.1rem; border:1px solid #27364b;
        border-radius:18px; background:linear-gradient(120deg,#14253d,#111827 62%,#17263a);}
    .news-eyebrow {color:#7dd3fc; font-size:.77rem; font-weight:700; letter-spacing:.14em;}
    .news-hero h1 {margin:.42rem 0 .25rem; font-size:2rem;}
    .news-hero p {margin:0; color:#9caec2;}
    </style>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="news-hero"><div class="news-eyebrow">MARKET NEWS & POLICY</div>'
    '<h1>资讯</h1>'
    '<p>跟踪全球宏观经济、美联储决议、中国货币政策与重点行业市场事件。</p></div>',
    unsafe_allow_html=True,
)
st.caption(
    "选择一个专题只查看对应资讯；标题可直接点击打开。数据每 10 分钟缓存一次，"
    "也可手动刷新获取最新发布。"
)

selected_categories = st.pills(
    "资讯专题",
    NEWS_CATEGORIES,
    selection_mode="single",
)

source_col, search_col, refresh_col = st.columns(
    [1, 3, 1], vertical_alignment="bottom"
)
with source_col:
    with st.popover("来源筛选", icon=":material/tune:", width="stretch"):
        selected_providers = st.multiselect(
            "资讯来源",
            NEWS_PROVIDERS,
            default=list(NEWS_PROVIDERS),
            key="news_provider_filter",
        )
with search_col:
    search_query = st.text_input(
        "搜索标题或来源",
        placeholder="输入关键词筛选标题、发布机构或相关标的",
        label_visibility="collapsed",
        key="news_search_query",
    )
with refresh_col:
    refresh_news = st.button(
        "刷新资讯", icon=":material/refresh:", type="primary", width="stretch"
    )

if refresh_news:
    fetch_market_news.clear()

with st.spinner("正在获取多源资讯与政策信息..."):
    market_news, market_news_errors, news_checked_at = fetch_market_news()

news_time = news_checked_at.astimezone(ZoneInfo("Asia/Shanghai"))
st.caption(f"最近刷新（北京时间）：{news_time:%Y-%m-%d %H:%M:%S}")

if selected_categories:
    market_news = market_news.loc[
        market_news["categories"].map(lambda categories: selected_categories in categories)
    ]
if selected_providers:
    market_news = market_news.loc[
        market_news["provider"].isin(selected_providers)
    ]
else:
    market_news = market_news.iloc[0:0]
if search_query.strip():
    query = search_query.strip().casefold()
    searchable = (
        market_news["title"].fillna("")
        + " "
        + market_news["publisher"].fillna("")
        + " "
        + market_news["related_tickers"].fillna("")
    ).str.casefold()
    market_news = market_news.loc[searchable.str.contains(query, regex=False)]

if market_news.empty:
    if market_news_errors:
        st.warning("暂时无法获取资讯：" + "；".join(market_news_errors))
    else:
        st.info("当前分类和来源没有匹配的近 7 天资讯，请调整筛选或刷新。")
else:
    st.caption(
        f"找到 {len(market_news)} 条资讯，按发布时间排序；当前显示前 "
        f"{min(len(market_news), 20)} 条。"
    )
    for _, article in market_news.head(20).iterrows():
        published_at = pd.Timestamp(article["published_at"]).tz_convert(
            "Asia/Shanghai"
        )
        with st.container(border=True):
            st.caption(
                f"专题：{' · '.join(article['categories'])}"
            )
            st.link_button(
                article["title"],
                article["url"],
                width="stretch",
                type="tertiary",
            )
            st.caption(
                f"来源：{article['publisher']}　·　"
                f"北京时间 {published_at:%Y-%m-%d %H:%M}"
            )
            if article["related_tickers"]:
                st.caption(f"相关标的：{article['related_tickers']}")

if market_news_errors and not market_news.empty:
    st.warning("部分公开新闻源暂不可用：" + "；".join(market_news_errors))
st.caption(
    "全球媒体资讯仅作市场参考。美联储、中国人民银行、国家统计局条目链接至其官方页面；"
    "政策与数据请以官方原文为准。"
)
