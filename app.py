import streamlit as st

from src.database.schema import initialize_database


initialize_database()


st.set_page_config(
    page_title="Si Market助手",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --surface-border: rgba(126, 170, 212, .2);
        --text-muted: #9bb0c8;
        --accent: #70e1f5;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 77% 4%, rgba(32, 115, 181, .2), transparent 38%),
            radial-gradient(ellipse at 2% 82%, rgba(16, 121, 139, .14), transparent 36%),
            radial-gradient(ellipse at 94% 92%, rgba(79, 70, 160, .09), transparent 32%),
            #0b1220 !important;
        background-size: 145% 145%, 160% 160%, 150% 150%, auto;
        overflow-x: hidden !important;
    }
    @keyframes hero-glow {
        0%, 100% { opacity: .45; transform: translate3d(0, 0, 0) scale(1); }
        50% { opacity: .8; transform: translate3d(-16px, 8px, 0) scale(1.08); }
    }
    @keyframes press-glow {
        0% { opacity: .72; background-size: 0 0; }
        100% { opacity: 0; background-size: 260% 260%; }
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stMain"] {
        margin-left: 0 !important;
        padding: 1.1rem 0 2.5rem 260px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    [data-testid="stMain"] .block-container {
        width: 100% !important;
        max-width: 1560px !important;
        box-sizing: border-box !important;
        padding: .9rem clamp(1.1rem, 3vw, 3rem) 3rem !important;
    }
    [data-testid="stMain"] h1 {
        letter-spacing: -.035em;
        line-height: 1.14;
    }
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        letter-spacing: -.02em;
    }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {
        color: var(--text-muted);
    }
    [data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg, rgba(23, 41, 62, .9), rgba(13, 26, 42, .94));
        border: 1px solid var(--surface-border);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 30px rgba(2, 8, 23, .16), inset 0 1px rgba(255,255,255,.025);
        transition: transform .24s cubic-bezier(.2,.8,.2,1), border-color .24s ease,
            box-shadow .24s ease, background .24s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: rgba(102, 217, 239, .4);
        background: linear-gradient(145deg, rgba(25, 50, 73, .96), rgba(14, 31, 49, .98));
        box-shadow: 0 18px 38px rgba(2, 8, 23, .28), 0 0 24px rgba(34, 211, 238, .055);
    }
    [data-testid="stMetricLabel"] {
        color: #9aacc2 !important;
    }
    [data-testid="stMetricValue"] {
        font-variant-numeric: tabular-nums;
        letter-spacing: -.035em;
    }
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button {
        position: relative;
        overflow: hidden;
        border-radius: 11px;
        transition: transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s ease,
            border-color .2s ease, background .2s ease, filter .2s ease;
    }
    [data-testid="stButton"] button:after,
    [data-testid="stFormSubmitButton"] button:after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        opacity: 0;
        pointer-events: none;
        background: radial-gradient(circle, rgba(164, 243, 255, .46) 0, rgba(96, 165, 250, .2) 20%, transparent 62%) 50% 50% / 0 0 no-repeat;
    }
    [data-testid="stButton"] button:active:after,
    [data-testid="stFormSubmitButton"] button:active:after {
        animation: press-glow .48s ease-out;
    }
    [data-testid="stButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(2, 8, 23, .3), 0 0 18px rgba(96, 165, 250, .14);
    }
    [data-testid="stButton"] button:active,
    [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0) scale(.985);
        filter: brightness(1.12);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        border-radius: 11px;
        transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {
        border-color: rgba(112, 225, 245, .58);
        box-shadow: 0 0 0 3px rgba(34, 211, 238, .11);
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: .4rem;
        border-bottom: 1px solid rgba(148, 163, 184, .13);
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1rem;
        border-radius: 10px 10px 0 0;
        color: #9aacc2;
        transition: color .16s ease, background .16s ease;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: #e7f0fb;
        background: rgba(96, 165, 250, .07);
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        position: relative;
        overflow: hidden;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:active {
        background: radial-gradient(circle at center, rgba(103, 232, 249, .2), rgba(96, 165, 250, .07) 42%, transparent 76%);
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--surface-border);
        border-radius: 14px;
        overflow: hidden;
    }
    [data-testid="stPlotlyChart"] {
        border-radius: 14px;
    }
    [data-testid="stAlert"] {
        border-radius: 13px;
    }

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
        padding: 1rem .8rem;
        box-sizing: border-box;
        background:
            radial-gradient(ellipse at 0% 0%, rgba(37, 99, 170, .13), transparent 42%),
            linear-gradient(180deg, rgba(14, 27, 45, .98), rgba(9, 18, 31, .99));
        border-right: 1px solid rgba(126, 170, 212, .17);
        box-shadow: 10px 0 42px rgba(2, 8, 23, .24);
        backdrop-filter: blur(18px);
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: .62rem;
        padding: .55rem .45rem .75rem;
        margin-bottom: .55rem;
        border-bottom: 1px solid rgba(148, 163, 184, .13);
    }
    .brand-mark {
        display: grid;
        position: relative;
        flex: 0 0 40px;
        width: 40px;
        height: 40px;
        place-items: center;
        overflow: hidden;
        border: 1px solid rgba(147, 197, 253, .45);
        border-radius: 13px;
        background: linear-gradient(145deg, #2563eb, #22d3ee);
        color: white;
        font-size: 1.02rem;
        font-weight: 800;
        letter-spacing: -.06em;
        box-shadow: 0 8px 24px rgba(37, 99, 235, .32), 0 0 26px rgba(34, 211, 238, .14);
    }
    .brand-mark:after {
        content: "";
        position: absolute;
        top: -35%;
        left: 0;
        width: 45%;
        height: 170%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.3), transparent);
        animation: logo-sheen 6s ease-in-out infinite;
        pointer-events: none;
    }
    @keyframes logo-sheen {
        0%, 70% { transform: translateX(-140%) rotate(25deg); }
        100% { transform: translateX(180%) rotate(25deg); }
    }
    .brand-decoration {
        position: relative;
        display: grid;
        flex: 0 0 38px;
        width: 38px;
        height: 38px;
        margin-left: auto;
        place-items: center;
        border: 1px solid rgba(125, 232, 255, .58);
        border-radius: 50%;
        background:
            radial-gradient(circle at 36% 28%, rgba(103, 232, 249, .18), transparent 48%),
            linear-gradient(145deg, rgba(19, 48, 73, .94), rgba(10, 22, 39, .96));
        box-shadow: 0 0 22px rgba(34, 211, 238, .22), inset 0 0 14px rgba(96, 165, 250, .12);
        pointer-events: none;
    }
    .brand-decoration:before {
        content: "";
        position: absolute;
        inset: 5px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(34, 211, 238, .22), rgba(59, 130, 246, .08) 52%, transparent 75%);
        filter: blur(3px);
        animation: brand-core-breathe 3.8s ease-in-out infinite;
    }
    .brand-decoration-track {
        position: absolute;
        width: 30px;
        height: 19px;
        border: 1px solid rgba(125, 232, 255, .72);
        border-radius: 50%;
        transform: rotate(-34deg);
        animation: brand-ring-turn 16s linear infinite;
    }
    .brand-decoration-track-two {
        width: 21px;
        height: 30px;
        border-color: rgba(167, 139, 250, .64);
        border-style: dashed;
        animation: brand-ring-turn-reverse 21s linear infinite;
    }
    .brand-decoration-dot {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 6px;
        height: 6px;
        margin: -3px 0 0 -3px;
        border-radius: 50%;
        background: #d4fbff;
        box-shadow: 0 0 11px rgba(103, 232, 249, .98);
        animation: brand-dot-orbit 7s linear infinite;
    }
    .brand-decoration-core {
        position: relative;
        z-index: 1;
        display: grid;
        width: 16px;
        height: 16px;
        place-items: center;
        border: 1px solid rgba(190, 242, 255, .8);
        border-radius: 50%;
        background: radial-gradient(circle at 34% 25%, #d7fbff, #49c1e4 43%, #24609c 78%);
        box-shadow: 0 0 13px rgba(103, 232, 249, .58), inset 0 0 5px rgba(255, 255, 255, .6);
    }
    @keyframes brand-ring-turn {
        to { transform: rotate(326deg); }
    }
    @keyframes brand-dot-orbit {
        to { transform: rotate(360deg) translateX(15px); }
    }
    @keyframes brand-ring-turn-reverse {
        to { transform: rotate(-326deg); }
    }
    @keyframes brand-core-breathe {
        0%, 100% { opacity: .42; transform: scale(.78); }
        50% { opacity: .95; transform: scale(1.08); }
    }
    .brand-copy {
        flex: 1 1 auto;
        min-width: 0;
    }
    .brand-name {
        color: #f1f5f9;
        font-family: Arial, "Microsoft YaHei", sans-serif;
        font-size: 1.02rem;
        font-style: normal;
        font-weight: 700;
        letter-spacing: 0;
        line-height: 1.3;
        transform: none;
    }
    .brand-subtitle {
        margin-top: .13rem;
        color: #8193aa;
        font-family: Arial, "Microsoft YaHei", sans-serif;
        font-size: .57rem;
        font-style: normal;
        letter-spacing: -.025em;
        line-height: 1.35;
        white-space: nowrap;
        text-transform: none;
        transform: none;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        width: 100%;
        min-height: 2.65rem;
        margin: .16rem 0;
        padding: .62rem .8rem;
        border: 1px solid transparent;
        border-radius: 11px;
        color: #F8FAFC !important;
        opacity: 1 !important;
        font-family: sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        text-decoration: none !important;
        text-align: left !important;
        box-sizing: border-box;
        transition: background .22s ease, border-color .22s ease, box-shadow .22s ease,
            color .22s ease, filter .22s ease;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a > span:first-child {
        display: grid !important;
        flex: 0 0 1.45rem;
        width: 1.45rem;
        place-items: center;
        color: #829bb7 !important;
        transition: color .2s ease, filter .2s ease;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a > span:last-child {
        flex: 1 1 auto;
        width: auto;
        min-width: 0;
        margin-left: .45rem;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        width: auto !important;
        color: #F8FAFC !important;
        opacity: 1 !important;
        font-family: sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        transform: none !important;
        line-height: 1.4 !important;
        text-align: left !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] [data-testid="stIconMaterial"] {
        display: inline-block !important;
        color: inherit !important;
        font-size: 1.2rem !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:hover {
        background: linear-gradient(105deg, rgba(34, 91, 133, .48), rgba(24, 55, 80, .62));
        border-color: rgba(112, 225, 245, .28);
        box-shadow: inset 0 0 20px rgba(34, 211, 238, .055), 0 5px 16px rgba(2, 8, 23, .16);
        filter: brightness(1.08);
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        opacity: 0;
        pointer-events: none;
        background: radial-gradient(circle, rgba(103, 232, 249, .28) 0, rgba(59, 130, 246, .14) 24%, transparent 64%) 50% 50% / 0 0 no-repeat;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:active:after {
        animation: press-glow .5s ease-out;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:hover > span:first-child {
        color: #7dd3fc !important;
        filter: drop-shadow(0 0 5px rgba(34, 211, 238, .45));
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a[aria-current="page"] {
        background: linear-gradient(105deg, rgba(25, 128, 158, .31), rgba(28, 63, 91, .7));
        border-color: rgba(112, 225, 245, .32);
        box-shadow: inset 3px 0 0 #70e1f5, 0 7px 22px rgba(4, 12, 24, .24);
        color: #FFFFFF !important;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a:focus-visible,
    [data-testid="stButton"] button:focus-visible,
    [data-testid="stFormSubmitButton"] button:focus-visible {
        outline: 2px solid rgba(112, 225, 245, .85) !important;
        outline-offset: 2px;
    }
    .st-key-fixed_nav [data-testid="stPageLink"] a[aria-current="page"] > span:first-child {
        color: #8be9f4 !important;
        filter: drop-shadow(0 0 6px rgba(34, 211, 238, .48));
    }
    [data-testid="stMain"] h1 {
        color: #f4f8ff;
        background: linear-gradient(105deg, #f5f8ff 0%, #c8e7fb 58%, #8be9f4 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 4px 20px rgba(34, 211, 238, .08));
    }
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(126, 170, 212, .2) !important;
        border-radius: 16px !important;
        background: linear-gradient(145deg, rgba(18, 34, 54, .58), rgba(11, 23, 38, .48));
        box-shadow: inset 0 1px rgba(255, 255, 255, .025), 0 12px 32px rgba(2, 8, 23, .1);
        transition: border-color .22s ease, box-shadow .22s ease, background .22s ease;
    }
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(112, 225, 245, .3) !important;
        box-shadow: inset 0 1px rgba(255, 255, 255, .035), 0 16px 38px rgba(2, 8, 23, .18);
    }
    .market-clock-card {
        display: flex;
        width: 100%;
        min-width: 0;
        box-sizing: border-box;
        align-items: center;
        justify-content: flex-end;
        gap: .85rem;
        min-height: 3.45rem;
        padding: .55rem .85rem;
        border: 1px solid rgba(126, 170, 212, .19);
        border-radius: 14px;
        background: linear-gradient(115deg, rgba(17, 35, 55, .9), rgba(14, 28, 46, .8));
        box-shadow: inset 0 1px rgba(255,255,255,.03), 0 8px 24px rgba(2,8,23,.13);
    }
    @media (min-width: 1101px) {
        .market-clock-card {
            justify-content: space-between;
        }
    }
    .market-clock-status {
        display: inline-flex;
        align-items: center;
        gap: .48rem;
        flex: 0 0 auto;
        padding: .38rem .62rem;
        border: 1px solid rgba(148, 163, 184, .16);
        border-radius: 999px;
        background: rgba(148, 163, 184, .08);
        color: #bdcbdc;
        font-size: .76rem;
        font-weight: 650;
        white-space: nowrap;
    }
    .market-clock-status:before {
        content: "";
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #94a3b8;
        box-shadow: 0 0 9px rgba(148, 163, 184, .5);
    }
    .market-clock-status.is-open {
        color: #a4f3d0;
        border-color: rgba(52, 211, 153, .24);
        background: rgba(16, 185, 129, .09);
    }
    .market-clock-status.is-open:before {
        background: #34d399;
        box-shadow: 0 0 10px rgba(52, 211, 153, .76);
        animation: market-live-pulse 2s ease-in-out infinite;
    }
    .market-clock-status.is-session {
        color: #c4e4ff;
        border-color: rgba(96, 165, 250, .22);
        background: rgba(59, 130, 246, .09);
    }
    .market-clock-status.is-session:before {
        background: #60a5fa;
        box-shadow: 0 0 9px rgba(96, 165, 250, .62);
    }
    .market-clock-time {
        color: #9fb2c9;
        font-size: .73rem;
        font-variant-numeric: tabular-nums;
        letter-spacing: .015em;
        white-space: nowrap;
    }
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        text-wrap: balance;
    }
    [data-testid="stMain"] p {
        text-align: left;
        text-wrap: pretty;
    }
    @keyframes market-live-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, .48); }
        50% { box-shadow: 0 0 0 5px rgba(52, 211, 153, 0); }
    }
    .nav-footnote {
        position: relative;
        margin: .8rem .1rem 0;
        padding: .75rem .8rem;
        border: 1px solid rgba(148, 163, 184, .12);
        border-radius: 11px;
        background: rgba(22, 36, 58, .54);
        color: #8193aa;
        font-size: .69rem;
        line-height: 1.55;
    }
    @media (max-width: 1100px) and (min-width: 721px) {
        .st-key-a-share-page-header [data-testid="stColumn"],
        .st-key-us-market-page-header [data-testid="stColumn"] {
            min-width: 0 !important;
        }
        .market-clock-card {
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: .35rem .6rem;
        }
        .market-clock-time {
            flex: 1 1 135px;
            min-width: 0;
            line-height: 1.35;
            text-align: right;
            white-space: normal;
            overflow-wrap: anywhere;
        }
    }
    @media (max-width: 720px) {
        .st-key-fixed_nav {
            position: relative;
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            align-items: center;
            gap: .62rem .55rem;
            width: 100%;
            height: auto;
            padding: .7rem .9rem .8rem;
            border-right: 0;
            border-bottom: 1px solid rgba(148, 163, 184, .13);
            margin-left: -12.6px !important;
            width: calc(100% + 25.2px) !important;
            max-width: none !important;
        }
        .st-key-fixed_nav > [data-testid="stElementContainer"] {
            min-width: 0;
            margin: 0 !important;
        }
        .st-key-a-share-page-header [data-testid="stHorizontalBlock"],
        .st-key-us-market-page-header [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: .15rem !important;
        }
        .st-key-a-share-page-header [data-testid="stColumn"],
        .st-key-us-market-page-header [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        .market-clock-card {
            justify-content: space-between;
            min-height: 3.2rem;
            margin-top: .1rem;
            padding: .5rem .72rem;
        }
        .market-clock-time { font-size: .7rem; }
        .st-key-fixed_nav > [data-testid="stElementContainer"]:first-child,
        .st-key-fixed_nav > [data-testid="stElementContainer"]:last-child {
            grid-column: 1 / -1;
        }
        .brand-lockup { padding: .25rem .25rem .75rem; margin-bottom: .4rem; }
        .brand-mark { width: 36px; height: 36px; flex-basis: 36px; border-radius: 11px; }
        .brand-decoration { width: 36px; height: 36px; flex-basis: 36px; }
        .brand-decoration-track { width: 28px; height: 18px; }
        .brand-decoration-track-two { width: 20px; height: 28px; }
        .nav-footnote { display: none; }
        .st-key-fixed_nav [data-testid="stPageLink"] a {
            min-height: 2.7rem;
            margin: .08rem 0;
            padding: .62rem .78rem;
            border-radius: 12px;
            font-size: 14px !important;
        }
        .st-key-fixed_nav [data-testid="stPageLink"] [data-testid="stMarkdownContainer"] p {
            font-size: 14px !important;
        }
        .st-key-fixed_nav [data-testid="stPageLink"] a > span:first-child { flex-basis: 1.5rem; }
        .st-key-fixed_nav [data-testid="stPageLink"] a > span:last-child { margin-left: .38rem; }
        [data-testid="stMain"] {
            padding: .25rem 0 1.75rem !important;
        }
        [data-testid="stMain"] .block-container {
            padding: 1rem 1rem 2.5rem !important;
        }
        [data-testid="stMain"] h1 {
            font-size: clamp(1.65rem, 7vw, 2rem);
            line-height: 1.22;
        }
        [data-testid="stMain"] h2 { font-size: 1.35rem; }
        [data-testid="stMain"] h3 { font-size: 1.1rem; }
        [data-testid="stMain"] p {
            line-height: 1.7;
            text-align: left;
            text-wrap: pretty;
        }
        [data-testid="stMain"] [data-testid="stCaptionContainer"] {
            line-height: 1.55;
        }
        [data-testid="stMetric"] {
            padding: .9rem 1rem;
            border-radius: 15px;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            min-height: 2.9rem;
            padding: 0 .8rem;
        }
        [data-testid="stDataFrame"],
        [data-testid="stPlotlyChart"] {
            max-width: 100%;
            overflow-x: auto;
        }
    }
    @media (max-width: 380px) {
        .st-key-fixed_nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .st-key-fixed_nav [data-testid="stPageLink"] a { padding-right: .55rem; padding-left: .55rem; }
        [data-testid="stMain"] .block-container { padding-right: .8rem !important; padding-left: .8rem !important; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

page_links = [
    (
        st.Page(
            "pages/1_市场观察.py",
            title="Market",
            icon=":material/candlestick_chart:",
        ),
        "Market",
    ),
    (
        st.Page("pages/8_市场资讯.py", title="资讯", icon=":material/newspaper:"),
        "资讯",
    ),
    (st.Page("pages/2_个股研究.py", title="A股", icon=":material/manage_search:"), "A股"),
    (st.Page("pages/5_crypto.py", title="Crypto", icon=":material/currency_bitcoin:"), "Crypto"),
    (st.Page("pages/6_us_stocks.py", title="美股", icon=":material/monitoring:"), "美股"),
    (st.Page("pages/3_我的股票池.py", title="自选", icon=":material/bookmark:"), "自选"),
    (st.Page("pages/4_研究报告.py", title="基础分析", icon=":material/description:"), "基础分析"),
    (st.Page("pages/7_si_intelligence.py", title="Si智能", icon=":material/auto_awesome:"), "Si智能"),
]
pages = [page for page, _ in page_links]

with st.container(key="fixed_nav"):
    st.markdown(
        '<div class="brand-lockup">'
        '<div class="brand-mark">Si</div>'
        '<div class="brand-copy"><div class="brand-name">Market助手</div>'
        '<div class="brand-subtitle">market research workspace</div></div>'
        '<div class="brand-decoration" aria-hidden="true">'
        '<span class="brand-decoration-track"></span>'
        '<span class="brand-decoration-track brand-decoration-track-two"></span>'
        '<span class="brand-decoration-dot"></span>'
        '<span class="brand-decoration-core"></span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    for page, label in page_links:
        st.page_link(page, label=label, width="stretch")
    st.markdown(
        '<div class="nav-footnote">公开数据 · 辅助研究<br>行情可能延迟，不构成投资建议</div>',
        unsafe_allow_html=True,
    )

navigation = st.navigation(pages, position="hidden")
navigation.run()
