import streamlit as st


st.markdown(
    """<style>
    .si-lab-hero {
        position: relative;
        overflow: hidden;
        min-height: 245px;
        margin: .15rem 0 1.25rem;
        padding: 2rem 2.15rem;
        border: 1px solid rgba(103, 232, 249, .22);
        border-radius: 22px;
        background:
            radial-gradient(ellipse at 83% 36%, rgba(34, 211, 238, .18), transparent 31%),
            radial-gradient(ellipse at 100% 0%, rgba(59, 130, 246, .18), transparent 45%),
            linear-gradient(115deg, #101e31 4%, #10263a 55%, #101a2b);
        box-shadow: 0 20px 55px rgba(2, 8, 23, .32), inset 0 1px rgba(255,255,255,.045);
    }
    .si-orb-stage {
        position: absolute;
        right: 4%;
        top: 50%;
        width: 300px;
        height: 300px;
        transform: translateY(-50%);
        pointer-events: none;
    }
    .si-orb-glow {
        position: absolute;
        inset: 18%;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(61, 216, 247, .3) 0, rgba(52, 142, 255, .17) 28%, rgba(90, 80, 210, .1) 48%, transparent 72%);
        filter: blur(9px);
        animation: ai-core-breathe 4.8s ease-in-out infinite;
    }
    .si-orb-ring {
        position: absolute;
        inset: 11%;
        border: 1px solid rgba(103, 232, 249, .28);
        border-radius: 50%;
        box-shadow: inset 0 0 24px rgba(34, 211, 238, .045), 0 0 24px rgba(34, 211, 238, .08);
        animation: ai-orbit 18s linear infinite;
    }
    .si-orb-ring:before {
        content: "";
        position: absolute;
        top: 12%;
        left: 21%;
        width: 9px;
        height: 9px;
        border: 2px solid #b9f6ff;
        border-radius: 50%;
        background: #38bdf8;
        box-shadow: 0 0 14px rgba(103, 232, 249, .95);
    }
    .si-orb-ring-two {
        inset: 22%;
        border-color: rgba(129, 140, 248, .34);
        border-style: dashed;
        animation-duration: 25s;
        animation-direction: reverse;
    }
    .si-orb-ring-two:before {
        top: auto;
        bottom: 8%;
        left: 18%;
        width: 6px;
        height: 6px;
        border: 0;
        background: #a78bfa;
        box-shadow: 0 0 14px rgba(167, 139, 250, .9);
    }
    .si-orb-ring-three {
        inset: 34%;
        border-color: rgba(103, 232, 249, .18);
        border-style: dotted;
        animation-duration: 13s;
    }
    .si-orb-core {
        position: absolute;
        top: 50%;
        left: 50%;
        display: grid;
        width: 94px;
        height: 94px;
        place-items: center;
        border: 1px solid rgba(190, 242, 255, .48);
        border-radius: 50%;
        background: radial-gradient(circle at 34% 25%, rgba(126, 245, 255, .92), rgba(49, 153, 226, .74) 30%, rgba(37, 73, 153, .8) 68%, rgba(18, 38, 70, .94));
        box-shadow: 0 0 26px rgba(34, 211, 238, .36), 0 0 70px rgba(59, 130, 246, .26), inset 0 0 20px rgba(255,255,255,.25);
        color: #f4fdff;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -.08em;
        text-shadow: 0 1px 10px rgba(5, 20, 48, .7);
        transform: translate(-50%, -50%);
        animation: ai-core-float 5.5s ease-in-out infinite;
    }
    @keyframes ai-orbit {
        to { rotate: 360deg; }
    }
    @keyframes ai-core-breathe {
        0%, 100% { opacity: .62; scale: .88; }
        50% { opacity: 1; scale: 1.08; }
    }
    @keyframes ai-core-float {
        0%, 100% { translate: 0 2px; filter: brightness(.94); }
        50% { translate: 0 -5px; filter: brightness(1.13); }
    }
    .si-lab-content {position: relative; z-index: 2; max-width: 680px;}
    .si-lab-kicker {
        display: inline-flex;
        align-items: center;
        gap: .55rem;
        color: #8be9f4;
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .16em;
    }
    .si-lab-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #67e8f9;
        box-shadow: 0 0 13px rgba(103, 232, 249, .8);
    }
    .si-lab-content h1 {
        margin: .8rem 0 .55rem;
        color: #f1f7ff;
        font-size: clamp(2rem, 4vw, 2.7rem);
        letter-spacing: -.045em;
    }
    .si-lab-content p {
        max-width: 570px;
        margin: 0;
        color: #a9bad0;
        font-size: .98rem;
        line-height: 1.75;
    }
    .si-lab-status {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        margin-top: 1.2rem;
        padding: .43rem .75rem;
        border: 1px solid rgba(103, 232, 249, .2);
        border-radius: 999px;
        background: rgba(8, 27, 43, .5);
        color: #b6eaf1;
        font-size: .78rem;
    }
    .si-lab-section {
        margin: 1.5rem 0 .8rem;
        color: #d9e6f5;
        font-size: 1.05rem;
        font-weight: 650;
    }
    .si-roadmap {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .85rem;
    }
    .si-roadmap-card {
        min-height: 155px;
        padding: 1.05rem 1.1rem;
        border: 1px solid rgba(125, 162, 205, .17);
        border-radius: 16px;
        background: linear-gradient(145deg, rgba(19, 36, 57, .86), rgba(13, 25, 41, .8));
        transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
    }
    .si-roadmap-card:hover {
        transform: translateY(-4px) scale(1.012);
        border-color: rgba(103, 232, 249, .4);
        background: linear-gradient(145deg, rgba(23, 52, 76, .92), rgba(14, 31, 50, .9));
        box-shadow: 0 15px 32px rgba(2, 8, 23, .27), 0 0 26px rgba(34, 211, 238, .075);
    }
    .si-roadmap-card:active {
        background: radial-gradient(circle at center, rgba(103, 232, 249, .17), transparent 72%),
            linear-gradient(145deg, rgba(19, 36, 57, .86), rgba(13, 25, 41, .8));
    }
    .si-roadmap-num {color: #67e8f9; font-size: .72rem; font-weight: 750; letter-spacing: .12em;}
    .si-roadmap-title {margin: .55rem 0 .35rem; color: #e7f0fb; font-size: .97rem; font-weight: 650;}
    .si-roadmap-copy {color: #91a5bd; font-size: .8rem; line-height: 1.6;}
    @media (max-width: 800px) {
        .si-lab-hero {min-height: 220px; margin-bottom: 1.7rem; padding: 1.7rem 1.3rem;}
        .si-orb-stage {right: -125px; opacity: .48; scale: .82;}
        .si-lab-content h1 {font-size: clamp(1.85rem, 8vw, 2.5rem); line-height: 1.2;}
        .si-lab-content p {font-size: .95rem; line-height: 1.8;}
        .si-lab-status {max-width: 100%; line-height: 1.45;}
        .si-lab-section {margin: 1.8rem 0 1rem;}
        .si-roadmap {grid-template-columns: 1fr; gap: .9rem;}
        .si-roadmap-card {min-height: auto; padding: 1.2rem 1.25rem;}
        .si-roadmap-title {margin-top: .65rem;}
        .si-roadmap-copy {font-size: .86rem; line-height: 1.75;}
    }
    @media (prefers-reduced-motion: reduce) {
        .si-orb-ring, .si-orb-glow, .si-orb-core {animation: none;}
        .si-roadmap-card {transition: none;}
    }
    </style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<section class="si-lab-hero">
      <div class="si-orb-stage" aria-hidden="true">
        <div class="si-orb-glow"></div>
        <div class="si-orb-ring"></div>
        <div class="si-orb-ring si-orb-ring-two"></div>
        <div class="si-orb-ring si-orb-ring-three"></div>
        <div class="si-orb-core">Si</div>
      </div>
      <div class="si-lab-content">
        <div class="si-lab-kicker"><span class="si-lab-dot"></span>SI INTELLIGENCE LAB</div>
        <h1>让市场信息，更容易读懂</h1>
        <p>Si智能仍在开发准备中。后续计划结合 SI 模型能力，把行情、资讯与个股研究串联起来，帮助你更快整理线索。</p>
        <div class="si-lab-status"><span class="si-lab-dot"></span>功能筹备中 · 当前尚未开放智能分析</div>
      </div>
    </section>
    <div class="si-lab-section">后续规划</div>
    <section class="si-roadmap">
      <article class="si-roadmap-card">
        <div class="si-roadmap-num">01 · MARKET</div>
        <div class="si-roadmap-title">市场脉络整理</div>
        <div class="si-roadmap-copy">尝试把指数变化、市场热点与重要事件放在一起梳理。</div>
      </article>
      <article class="si-roadmap-card">
        <div class="si-roadmap-num">02 · RESEARCH</div>
        <div class="si-roadmap-title">个股研究辅助</div>
        <div class="si-roadmap-copy">围绕公开行情和基本资料，辅助整理个股研究要点。</div>
      </article>
      <article class="si-roadmap-card">
        <div class="si-roadmap-num">03 · BRIEFING</div>
        <div class="si-roadmap-title">资讯摘要与线索</div>
        <div class="si-roadmap-copy">从公开资讯中提炼摘要，帮助发现值得进一步核实的线索。</div>
      </article>
    </section>""",
    unsafe_allow_html=True,
)
