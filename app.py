"""
AI Customer Support Triage — NovaCRM
Main Streamlit entry point with KPI header and sidebar navigation.
"""
# Cache buster: v2.1

import streamlit as st
import db

st.set_page_config(
    page_title="NovaCRM Support Triage",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"about": None},  # Hide about menu
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar dark gradient */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
    border-right: 1px solid #334155;
}

[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }

/* Main background */
.main .block-container { padding-top: 1rem; max-width: 1400px; }

/* KPI chips */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-chip {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    min-width: 160px;
    flex: 1;
}
.kpi-chip .label { font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
.kpi-chip .value { font-size: 1.8rem; font-weight: 700; color: #f1f5f9; line-height: 1.1; }
.kpi-chip .sub   { font-size: 0.72rem; color: #64748b; margin-top: 0.2rem; }
.kpi-chip.red    { border-color: #ef4444; }
.kpi-chip.red .value { color: #ef4444; }
.kpi-chip.green  { border-color: #10b981; }
.kpi-chip.green .value { color: #10b981; }
.kpi-chip.amber  { border-color: #f59e0b; }
.kpi-chip.amber .value { color: #f59e0b; }
.kpi-chip.blue   { border-color: #3b82f6; }
.kpi-chip.blue .value { color: #60a5fa; }

/* Urgency badges */
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em;
}
.badge-p0 { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.badge-p1 { background: #fff7ed; color: #d97706; border: 1px solid #fcd34d; }
.badge-p2 { background: #fefce8; color: #ca8a04; border: 1px solid #fde68a; }
.badge-p3 { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }

/* Status badges */
.status-open       { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; font-weight: 600; }
.status-in_progress{ background: #fdf4ff; color: #9333ea; border: 1px solid #e9d5ff; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; font-weight: 600; }
.status-resolved   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; font-weight: 600; }
.status-deflected  { background: #ecfdf5; color: #059669; border: 1px solid #6ee7b7; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; font-weight: 600; }
.status-escalated  { background: #fff1f2; color: #e11d48; border: 1px solid #fda4af; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; font-weight: 600; }

/* Category badges */
.cat-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.7rem; font-weight: 600;
}
.cat-Billing        { background: #fdf4ff; color: #7c3aed; }
.cat-Bug-Report     { background: #fff1f2; color: #e11d48; }
.cat-Integration    { background: #eff6ff; color: #1d4ed8; }
.cat-Onboarding     { background: #f0fdf4; color: #15803d; }
.cat-Account        { background: #fff7ed; color: #c2410c; }
.cat-Feature-Request{ background: #f0f9ff; color: #0369a1; }
.cat-Other          { background: #f8fafc; color: #475569; }

/* Card style */
.card {
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 1.25rem; margin-bottom: 1rem;
}

/* AI panel */
.ai-panel {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px solid #3b82f6;
    border-radius: 12px; padding: 1.25rem;
}
.ai-panel-title {
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: #60a5fa; font-weight: 700; margin-bottom: 1rem;
}
.confidence-bar-bg {
    background: #334155; border-radius: 4px; height: 6px; margin-top: 4px;
}
.confidence-bar-fill {
    background: linear-gradient(90deg, #3b82f6, #10b981);
    height: 6px; border-radius: 4px;
}

/* Dividers */
.section-divider { border: none; border-top: 1px solid #334155; margin: 1rem 0; }

/* Typography improvements */
h1 { font-size: 2rem !important; font-weight: 800 !important; letter-spacing: -0.02em !important; }
h2 { font-size: 1.4rem !important; font-weight: 700 !important; margin-top: 1.5rem !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; }

/* Streamlit button overrides */
.stButton button {
    background: #1e40af; color: white; border: none;
    border-radius: 6px; font-weight: 600; transition: all 0.2s ease;
}
.stButton button:hover {
    background: #1d4ed8; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3);
}
.stButton button:active { transform: translateY(0); }

/* Primary button variant */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6, #1e40af);
}
.stButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, #60a5fa, #1d4ed8);
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 8px; overflow: hidden;
    background: #0f172a !important;
}
[data-testid="stDataFrame"] [data-testid="stDataFrameCellHeader"] {
    background: #1e293b !important;
    color: #e2e8f0 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}
.streamlit-expanderHeader:hover {
    background-color: #1e293b !important;
}

/* Dark selectbox / multiselect */
.stSelectbox label, .stMultiSelect label { color: #94a3b8 !important; font-size: 0.8rem !important; }
.stSelectbox, .stMultiSelect { color: #e2e8f0 !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem !important;
}

/* Sidebar radio buttons (navigation) */
[data-testid="stSidebar"] .stRadio > label {
    padding: 0 !important;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 0.5rem !important;
}
[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent;
    padding: 0.6rem 0.8rem !important;
    margin-bottom: 0.4rem;
    border-radius: 6px;
    border: 1px solid transparent;
    transition: all 0.2s ease;
    color: #cbd5e1 !important;
    font-weight: 500;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #1e293b;
    border-color: #475569;
}
[data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {
    background: #1e3a8a;
    border-color: #3b82f6;
    color: #93c5fd !important;
    font-weight: 600;
    box-shadow: inset 0 0 0 1px #3b82f6;
}

/* Divider styling */
[data-testid="stSidebar"] hr {
    margin: 1rem 0 !important;
    border-color: #1e293b !important;
}
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# Auto-seed on first load (empty database)
if "db_seeded" not in st.session_state:
    if db.get_stats()["total"] == 0:
        try:
            import seed_data
            seed_data.seed()
            st.session_state["db_seeded"] = True
        except Exception as e:
            st.error(f"Failed to seed database: {e}")
    else:
        st.session_state["db_seeded"] = True


# ── Hide page selector with CSS ────────────────────────────────────────────
st.markdown("""
<style>
/* Aggressively hide Streamlit's page navigator */
[data-testid="stSidebar"] .stSelectbox { display: none !important; }
[data-testid="stSidebar"] > div > div:first-child > div { display: none !important; }
/* Hide button elements that might be part of the navigator */
[data-testid="stSidebar"] button { display: none !important; }
/* But show our buttons later */
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Header
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem 0;'>
        <div style='font-size:1.6rem; font-weight:800; color:#f1f5f9; letter-spacing:-0.03em; margin-bottom:0.25rem;'>
            🎯 NovaCRM
        </div>
        <div style='font-size:0.8rem; color:#60a5fa; font-weight:600;'>
            AI Support Triage
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation with icons
    st.markdown("<div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.12em; font-weight:700; margin-bottom:1rem;'>📍 Navigation</div>", unsafe_allow_html=True)

    nav_pages = {
        "📥 Ticket Inbox": "Ticket Inbox",
        "🔍 Ticket Detail": "Ticket Detail",
        "📊 Analytics": "Analytics",
        "⚙️ Settings": "Settings",
    }

    page = st.radio(
        "Navigate",
        list(nav_pages.values()),
        format_func=lambda x: [k for k, v in nav_pages.items() if v == x][0],
        label_visibility="collapsed",
    )

    st.divider()

    # Live Stats Section
    stats = db.get_stats()
    st.markdown("<div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.12em; font-weight:700; margin-bottom:0.8rem;'>📈 Live Metrics</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='background:#1a2a3a; border:1px solid #334155; border-radius:8px; padding:0.75rem; text-align:center;'>
            <div style='font-size:0.65rem; color:#94a3b8; margin-bottom:0.3rem;'>Total</div>
            <div style='font-size:1.4rem; font-weight:800; color:#60a5fa;'>{stats['total']}</div>
            <div style='font-size:0.6rem; color:#64748b;'>tickets</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        color = "#10b981" if stats["deflection_rate"] >= 15 else "#f59e0b"
        st.markdown(f"""
        <div style='background:#1a2a3a; border:1px solid #334155; border-radius:8px; padding:0.75rem; text-align:center;'>
            <div style='font-size:0.65rem; color:#94a3b8; margin-bottom:0.3rem;'>Deflection</div>
            <div style='font-size:1.4rem; font-weight:800; color:{color};'>{stats['deflection_rate']}%</div>
            <div style='font-size:0.6rem; color:#64748b;'>rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"""
        <div style='background:#1a2a3a; border:1px solid #334155; border-radius:8px; padding:0.75rem; text-align:center;'>
            <div style='font-size:0.65rem; color:#94a3b8; margin-bottom:0.3rem;'>Open</div>
            <div style='font-size:1.4rem; font-weight:800; color:#3b82f6;'>{stats['open']}</div>
            <div style='font-size:0.6rem; color:#64748b;'>awaiting</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        p0_color = "#ef4444" if stats["p0_open"] > 0 else "#10b981"
        st.markdown(f"""
        <div style='background:#1a2a3a; border:1px solid #334155; border-radius:8px; padding:0.75rem; text-align:center;'>
            <div style='font-size:0.65rem; color:#94a3b8; margin-bottom:0.3rem;'>Critical</div>
            <div style='font-size:1.4rem; font-weight:800; color:{p0_color};'>{stats['p0_open']}</div>
            <div style='font-size:0.6rem; color:#64748b;'>P0 open</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Footer
    st.markdown("""
    <div style='font-size:0.65rem; color:#64748b; text-align:center; padding-top:0.5rem;'>
        <div style='margin-bottom:0.25rem;'>Powered by GPT-5</div>
        <div style='font-weight:600; color:#60a5fa;'>NovaCRM v2.2</div>
    </div>
    """, unsafe_allow_html=True)


# ── Header KPIs ───────────────────────────────────────────────────────────────
stats = db.get_stats()

p0_class = "red" if stats["p0_open"] > 0 else "green"
defl_class = "green" if stats["deflection_rate"] >= 15 else "amber"

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-chip blue">
        <div class="label">Open Tickets</div>
        <div class="value">{stats['open']}</div>
        <div class="sub">Awaiting agent response</div>
    </div>
    <div class="kpi-chip {defl_class}">
        <div class="label">Deflection Rate</div>
        <div class="value">{stats['deflection_rate']}%</div>
        <div class="sub">Auto-resolved by KB</div>
    </div>
    <div class="kpi-chip green">
        <div class="label">Resolved</div>
        <div class="value">{stats['resolved']}</div>
        <div class="sub">Closed tickets</div>
    </div>
    <div class="kpi-chip {p0_class}">
        <div class="label">P0 Open</div>
        <div class="value">{stats['p0_open']}</div>
        <div class="sub">Critical / prod down</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Route to page ─────────────────────────────────────────────────────────────
if page == "Ticket Inbox":
    from pages import ticket_inbox
    ticket_inbox.render()

elif page == "Ticket Detail":
    from pages import ticket_detail
    ticket_detail.render()

elif page == "Analytics":
    from pages import analytics
    analytics.render()

elif page == "Settings":
    from pages import settings
    settings.render()
