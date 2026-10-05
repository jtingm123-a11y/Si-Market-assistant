import streamlit as st

from src.database.schema import initialize_database


initialize_database()


st.set_page_config(
    page_title="市场研究工作台",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Keep navigation in the same Streamlit tab and give every item one type scale. */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stBaseButton-headerNoPadding"],
    [data-testid="stExpandSidebarButton"] {
        display: none !important;
    }
    .st-key-fixed_nav {
        position: fixed;
        z-index: 999999;
        top: 0;
        left: 0;
        width: 260px;
        height: 100vh;
        padding: 1.25rem .7rem;
        box-sizing: border-box;
        background: #0F1928;
        border-right: 1px solid #26364D;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        width: 100%;
        min-height: 2.9rem;
        margin: .3rem 0;
        padding: .8rem 1rem;
        border: 1px solid transparent;
        border-radius: 12px;
        color: #F8FAFC !important;
        opacity: 1 !important;
        font-family: sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        text-decoration: none !important;
        text-align: left !important;
        box-sizing: border-box;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a > span:first-child {
        display: none !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a > span:last-child {
        flex: 1 1 auto;
        width: auto;
        min-width: 0;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        width: auto !important;
        color: #F8FAFC !important;
        opacity: 1 !important;
        font-family: sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        text-align: left !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] [data-testid="stIconMaterial"] {
        display: none !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:hover {
        background: linear-gradient(135deg, #1C3554, #162A43);
        border-color: #315176;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a[aria-current="page"] {
        background: linear-gradient(135deg, #34577F, #274568);
        border-color: #5279A5;
        box-shadow: 0 5px 14px rgba(4, 12, 24, .28);
        color: #FFFFFF !important;
    }
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
    }
    [data-testid="stMain"] {
        margin-left: 0 !important;
        padding-left: 260px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMain"] .block-container {
        width: 100% !important;
        max-width: none !important;
        box-sizing: border-box !important;
        padding-left: clamp(1rem, 2.2vw, 2.5rem) !important;
        padding-right: clamp(1rem, 2.2vw, 2.5rem) !important;
    }
    @media (max-width: 900px) {
        .st-key-fixed_nav {
            width: 210px;
        }
        [data-testid="stMain"] {
            padding-left: 210px !important;
        }
        .st-key-fixed_nav [data-testid="stPageLink"] a {
            font-size: 15px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

page_links = [
    (st.Page("pages/1_市场观察.py", title="市场观察", icon=":material/candlestick_chart:"), "市场观察"),
    (st.Page("pages/2_个股研究.py", title="A股", icon=":material/manage_search:"), "A股"),
    (st.Page("pages/5_crypto.py", title="Crypto", icon=":material/currency_bitcoin:"), "Crypto"),
    (st.Page("pages/6_us_stocks.py", title="美股", icon=":material/monitoring:"), "美股"),
    (st.Page("pages/3_我的股票池.py", title="自选观察", icon=":material/bookmark:"), "自选观察"),
    (st.Page("pages/4_研究报告.py", title="基础分析", icon=":material/description:"), "基础分析"),
    (st.Page("pages/7_si_intelligence.py", title="Si智能", icon=":material/auto_awesome:"), "Si智能"),
]
pages = [page for page, _ in page_links]

with st.container(key="fixed_nav"):
    for page, label in page_links:
        st.page_link(page, label=label, width="stretch")

navigation = st.navigation(pages, position="hidden")
navigation.run()
