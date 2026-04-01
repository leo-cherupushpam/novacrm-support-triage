"""
Analytics — Manager view (simplified).
Live metrics, status breakdown, and ROI estimate.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import db

BG      = "#0f172a"
CARD_BG = "#1e293b"
TEXT    = "#e2e8f0"
MUTED   = "#94a3b8"


def render():
    st.markdown("## Analytics Dashboard")
    st.markdown("<p style='color:#94a3b8; margin-top:-0.5rem; margin-bottom:1.5rem;'>Manager view · business metrics & AI performance</p>", unsafe_allow_html=True)

    tickets = db.get_all_tickets()
    if not tickets:
        st.info("No ticket data yet. Run `python seed_data.py` to seed the database.")
        return

    df = pd.DataFrame(tickets)
    stats = db.get_stats()

    # ── KPI Row ──────────────────────────────────────────────────────────────────
    _render_kpis(stats, tickets)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Charts Row 1: Category + Urgency ──────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        _chart_category(df)
    with col2:
        _chart_urgency(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 2: Status + Sentiment ──────────────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        _chart_status(df)
    with col4:
        _chart_sentiment(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KB Articles + Insights ───────────────────────────────────────────────────
    col5, col6 = st.columns([3, 2])
    with col5:
        _table_top_kb()
    with col6:
        _render_insights(df, stats)


# ── KPI Row ────────────────────────────────────────────────────────────────────

def _render_kpis(stats: dict, tickets: list):
    col1, col2, col3, col4, col5 = st.columns(5)

    def _kpi(col, label, value, sub, cls="blue"):
        col.markdown(f"""
        <div class='kpi-chip {cls}'>
            <div class='label'>{label}</div>
            <div class='value'>{value}</div>
            <div class='sub'>{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    p0_class = "red" if stats["p0_open"] > 0 else "green"
    defl_class = "green" if stats["deflection_rate"] >= 15 else "amber"

    _kpi(col1, "Total Tickets", stats["total"], "all time", "blue")
    _kpi(col2, "Deflection Rate", f"{stats['deflection_rate']}%", "auto-resolved by KB", defl_class)
    _kpi(col3, "Open Tickets", stats["open"], "awaiting agent", "blue")
    _kpi(col4, "Resolved", stats["resolved"], "closed tickets", "green")
    _kpi(col5, "P0 Open", stats["p0_open"], "critical / outage", p0_class)


# ── Simple Charts ──────────────────────────────────────────────────────────────────

def _chart_category(df: pd.DataFrame):
    st.markdown("#### Category Breakdown")
    cat_colors = {
        "Billing": "#a78bfa",
        "Bug Report": "#f87171",
        "Integration": "#60a5fa",
        "Onboarding": "#34d399",
        "Account": "#fb923c",
        "Feature Request": "#38bdf8",
        "Other": "#64748b",
    }

    counts = df["ai_category"].value_counts().head(7).reset_index()
    counts.columns = ["Category", "Count"]
    colors = [cat_colors.get(c, "#64748b") for c in counts["Category"]]

    fig = go.Figure(go.Bar(
        x=counts["Category"],
        y=counts["Count"],
        marker_color=colors,
        text=counts["Count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} tickets<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=MUTED, size=11),
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="transparent", linecolor="transparent"),
        yaxis=dict(gridcolor="#334155", linecolor="#334155"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _chart_urgency(df: pd.DataFrame):
    st.markdown("#### Urgency Distribution")
    order = ["P0", "P1", "P2", "P3"]
    urg_colors = {"P0": "#ef4444", "P1": "#f59e0b", "P2": "#eab308", "P3": "#22c55e"}

    counts = df["ai_urgency"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Urgency", "Count"]
    colors = [urg_colors[u] for u in counts["Urgency"]]

    fig = go.Figure(go.Bar(
        x=counts["Urgency"],
        y=counts["Count"],
        marker_color=colors,
        text=counts["Count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} tickets<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=MUTED, size=11),
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="transparent", linecolor="transparent"),
        yaxis=dict(gridcolor="#334155", linecolor="#334155"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _chart_status(df: pd.DataFrame):
    st.markdown("#### Status Breakdown")
    status_colors = {
        "OPEN": "#3b82f6",
        "IN_PROGRESS": "#9333ea",
        "RESOLVED": "#10b981",
        "DEFLECTED": "#06b6d4",
        "ESCALATED": "#ef4444",
    }

    counts = df["status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    counts["Status"] = counts["Status"].str.replace("_", " ")
    colors = [status_colors.get(s.replace(" ", "_"), "#64748b") for s in counts["Status"]]

    fig = go.Figure(go.Pie(
        labels=counts["Status"],
        values=counts["Count"],
        marker=dict(colors=colors, line=dict(color=BG, width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} tickets<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=MUTED, size=11),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def _chart_sentiment(df: pd.DataFrame):
    st.markdown("#### Sentiment Breakdown")
    sent_colors = {"ANGRY": "#ef4444", "FRUSTRATED": "#f59e0b", "NEUTRAL": "#64748b", "SATISFIED": "#10b981"}
    labels_map = {"ANGRY": "😡 Angry", "FRUSTRATED": "😟 Frustrated", "NEUTRAL": "😐 Neutral", "SATISFIED": "😊 Satisfied"}

    order = ["ANGRY", "FRUSTRATED", "NEUTRAL", "SATISFIED"]
    counts = df["ai_sentiment"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Sentiment", "Count"]
    counts["Label"] = counts["Sentiment"].map(labels_map)
    colors = [sent_colors[s] for s in counts["Sentiment"]]

    fig = go.Figure(go.Bar(
        x=counts["Label"],
        y=counts["Count"],
        marker_color=colors,
        text=counts["Count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} tickets<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=MUTED, size=11),
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor="transparent", linecolor="transparent"),
        yaxis=dict(gridcolor="#334155", linecolor="#334155"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── KB Articles Table ──────────────────────────────────────────────────────────────

def _table_top_kb():
    st.markdown("#### Top KB Articles by Usage")
    articles = db.get_kb_articles()
    if not articles:
        st.caption("No KB articles found.")
        return

    top = sorted(articles, key=lambda a: a.get("use_count", 0), reverse=True)[:8]
    df_kb = pd.DataFrame([{
        "Title": a["title"][:45] + ("…" if len(a["title"]) > 45 else ""),
        "Category": a["category"],
        "Uses": a.get("use_count", 0),
        "Tags": (a.get("tags") or "")[:30],
    } for a in top])

    st.dataframe(
        df_kb,
        use_container_width=True,
        hide_index=True,
        height=260,
    )


# ── Insights ───────────────────────────────────────────────────────────────────────

def _render_insights(df: pd.DataFrame, stats: dict):
    st.markdown("#### Key Metrics")

    # ROI estimate
    hours_saved = round(stats["deflected"] * 0.5, 1)
    cost_saved = round(hours_saved * 35, 0)

    st.markdown(f"""
    <div style='background:#022c22; border:1px solid #059669; border-radius:8px; padding:0.9rem; margin-bottom:0.5rem;'>
        <div style='color:#10b981; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.5rem;'>💰 ROI Estimate</div>
        <div style='color:#6ee7b7; font-size:0.82rem; line-height:1.5;'>
            <b>{stats['deflected']}</b> deflected<br>
            ≈ <b>{hours_saved}h</b> saved<br>
            ≈ <b>${cost_saved:,.0f}</b> saved
        </div>
        <div style='color:#047857; font-size:0.68rem; margin-top:6px;'>Based on $35/hr · 0.5h avg</div>
    </div>
    """, unsafe_allow_html=True)

    # Top category
    if not df.empty:
        top_cat = df["ai_category"].value_counts().idxmax()
        top_pct = int(df["ai_category"].value_counts().iloc[0] / len(df) * 100)
        st.markdown(f"""
        <div style='background:#0f172a; border-left:3px solid #60a5fa; padding:0.6rem 0.8rem; border-radius:0 6px 6px 0;'>
            <span style='color:#60a5fa; font-size:0.82rem; font-weight:500;'>📊 {top_cat} is top category ({top_pct}%)</span>
        </div>
        """, unsafe_allow_html=True)
