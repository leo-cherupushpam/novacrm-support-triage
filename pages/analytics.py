"""
Analytics — Manager view.
KPI row, ticket volume trend, category breakdown, urgency distribution,
day/hour heatmap, top KB articles, trend insight cards.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone, timedelta
import db

# ── Theme constants ────────────────────────────────────────────────────────────
BG      = "#0f172a"
CARD_BG = "#1e293b"
BORDER  = "#334155"
TEXT    = "#e2e8f0"
MUTED   = "#94a3b8"

CAT_COLORS = {
    "Billing":         "#a78bfa",
    "Bug Report":      "#f87171",
    "Integration":     "#60a5fa",
    "Onboarding":      "#34d399",
    "Account":         "#fb923c",
    "Feature Request": "#38bdf8",
    "Other":           "#64748b",
}

URG_COLORS = {
    "P0": "#ef4444",
    "P1": "#f59e0b",
    "P2": "#eab308",
    "P3": "#22c55e",
}


def _plotly_layout(title: str = "", height: int = 300) -> dict:
    return dict(
        title=dict(text=title, font=dict(color=TEXT, size=14)),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=MUTED, size=11),
        height=height,
        margin=dict(l=40, r=20, t=40 if title else 20, b=40),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
    )


# ── Main render ────────────────────────────────────────────────────────────────

def render():
    st.markdown("## Analytics Dashboard")
    st.markdown("<p style='color:#94a3b8; margin-top:-0.5rem; margin-bottom:1.5rem;'>Manager view · business metrics & AI performance</p>", unsafe_allow_html=True)

    tickets = db.get_all_tickets()
    if not tickets:
        st.info("No ticket data yet. Run `python seed_data.py` to seed the database.")
        return

    df = pd.DataFrame(tickets)

    # Resolve category to best available
    df["cat"]  = df.apply(lambda r: r.get("ai_category") or r.get("category") or "Other", axis=1)
    df["urg"]  = df.apply(lambda r: r.get("ai_urgency")  or r.get("urgency")  or "P3",   axis=1)
    df["sent"] = df.apply(lambda r: r.get("ai_sentiment") or r.get("sentiment") or "NEUTRAL", axis=1)

    # Parse timestamps
    def _parse_dt(s):
        try:
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except Exception:
            return None

    df["created_dt"] = df["created_at"].apply(_parse_dt)
    df = df.dropna(subset=["created_dt"])
    df["date"] = df["created_dt"].dt.date
    df["hour"] = df["created_dt"].dt.hour
    df["dow"]  = df["created_dt"].dt.dayofweek  # 0=Mon

    # ── KPI row ──────────────────────────────────────────────────────────────
    _render_kpis(df, tickets)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Charts row 1: Volume trend + Category donut ───────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        _chart_volume_trend(df)
    with col2:
        _chart_category_donut(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row 2: Urgency bar + Sentiment bar ─────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        _chart_urgency_bar(df)
    with col4:
        _chart_sentiment_bar(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Heatmap ──────────────────────────────────────────────────────────────
    _chart_heatmap(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bottom row: Top KB articles + Insight cards ───────────────────────────
    col5, col6 = st.columns([3, 2])
    with col5:
        _table_top_kb()
    with col6:
        _render_insights(df)


# ── KPI Row ────────────────────────────────────────────────────────────────────

def _render_kpis(df: pd.DataFrame, tickets: list):
    stats = db.get_stats()
    total = stats["total"]
    defl  = stats["deflection_rate"]

    # Avg response time (simulated: hours from created to updated on non-OPEN tickets)
    closed = df[df["status"].isin(["RESOLVED", "DEFLECTED"])]
    if not closed.empty and "updated_at" in df.columns:
        def _hours_diff(row):
            try:
                c = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
                u = datetime.fromisoformat(str(row["updated_at"]).replace("Z", "+00:00"))
                return (u - c).total_seconds() / 3600
            except Exception:
                return None
        closed = closed.copy()
        closed["resp_hours"] = closed.apply(_hours_diff, axis=1)
        avg_resp = closed["resp_hours"].dropna()
        avg_resp_str = f"{avg_resp.mean():.1f}h" if not avg_resp.empty else "—"
    else:
        avg_resp_str = "—"

    # SLA breach: P0/P1 open > 24h
    sla_breach = 0
    now = datetime.now(timezone.utc)
    for t in tickets:
        if t.get("status") == "OPEN" and (t.get("ai_urgency") or t.get("urgency")) in ("P0","P1"):
            try:
                created = datetime.fromisoformat(str(t["created_at"]).replace("Z","+00:00"))
                if (now - created).total_seconds() > 86400:
                    sla_breach += 1
            except Exception:
                pass

    # Estimated agent hours saved (deflected * 0.5h avg)
    hours_saved = round(stats["deflected"] * 0.5, 1)

    col1, col2, col3, col4, col5 = st.columns(5)

    def _kpi(col, label, value, sub, cls="blue"):
        col.markdown(f"""
        <div class='kpi-chip {cls}'>
            <div class='label'>{label}</div>
            <div class='value'>{value}</div>
            <div class='sub'>{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    _kpi(col1, "Total Tickets", total, "all time", "blue")
    _kpi(col2, "Deflection Rate", f"{defl}%", "auto-resolved by KB", "green" if defl >= 15 else "amber")
    _kpi(col3, "Avg Response", avg_resp_str, "time to resolve", "blue")
    _kpi(col4, "SLA Breaches", sla_breach, "P0/P1 open >24h", "red" if sla_breach > 0 else "green")
    _kpi(col5, "Hours Saved", f"{hours_saved}h", "est. agent time saved", "green")


# ── Charts ─────────────────────────────────────────────────────────────────────

def _chart_volume_trend(df: pd.DataFrame):
    st.markdown("#### Ticket Volume (last 30 days)")
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=30)
    recent = df[df["date"] >= cutoff].copy()

    if recent.empty:
        st.caption("No data in last 30 days.")
        return

    daily = recent.groupby("date").size().reset_index(name="count")
    deflected_daily = recent[recent["status"] == "DEFLECTED"].groupby("date").size().reset_index(name="deflected")
    daily = daily.merge(deflected_daily, on="date", how="left").fillna(0)
    daily["defl_rate"] = (daily["deflected"] / daily["count"] * 100).round(1)
    daily["date"] = pd.to_datetime(daily["date"])

    # Simple two-metric chart: bar for volume, line for deflection rate
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["date"], y=daily["count"],
        name="Total Tickets",
        marker_color="#3b82f6",
        opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["defl_rate"],
        name="Deflection Rate %",
        line=dict(color="#10b981", width=3),
        mode="lines+markers",
        marker=dict(size=6),
    ))

    layout = _plotly_layout(height=300)
    layout.update(barmode="overlay")
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def _chart_category_donut(df: pd.DataFrame):
    st.markdown("#### Category Breakdown")
    counts = df["cat"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]

    colors = [CAT_COLORS.get(c, "#64748b") for c in counts["Category"]]

    fig = go.Figure(go.Pie(
        labels=counts["Category"],
        values=counts["Count"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=BG, width=2)),
        textfont=dict(size=11),
    ))
    layout = _plotly_layout(height=300)
    layout.update(showlegend=True)
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def _chart_urgency_bar(df: pd.DataFrame):
    st.markdown("#### Urgency Distribution")
    order = ["P0", "P1", "P2", "P3"]
    counts = df["urg"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Urgency", "Count"]

    colors = [URG_COLORS[u] for u in counts["Urgency"]]
    fig = go.Figure(go.Bar(
        x=counts["Urgency"], y=counts["Count"],
        marker_color=colors,
        text=counts["Count"],
        textposition="outside",
        textfont=dict(color=TEXT),
    ))
    fig.update_layout(**_plotly_layout(height=260))
    st.plotly_chart(fig, use_container_width=True)


def _chart_sentiment_bar(df: pd.DataFrame):
    st.markdown("#### Sentiment Breakdown")
    order = ["ANGRY", "FRUSTRATED", "NEUTRAL", "SATISFIED"]
    colors_map = {"ANGRY": "#ef4444", "FRUSTRATED": "#f59e0b", "NEUTRAL": "#64748b", "SATISFIED": "#10b981"}
    labels_map = {"ANGRY": "😡 Angry", "FRUSTRATED": "😟 Frustrated", "NEUTRAL": "😐 Neutral", "SATISFIED": "😊 Satisfied"}

    counts = df["sent"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Sentiment", "Count"]
    counts["Label"] = counts["Sentiment"].map(labels_map)
    counts["Color"] = counts["Sentiment"].map(colors_map)

    fig = go.Figure(go.Bar(
        x=counts["Label"], y=counts["Count"],
        marker_color=counts["Color"],
        text=counts["Count"],
        textposition="outside",
        textfont=dict(color=TEXT),
    ))
    fig.update_layout(**_plotly_layout(height=260))
    st.plotly_chart(fig, use_container_width=True)


def _chart_heatmap(df: pd.DataFrame):
    st.markdown("#### Ticket Volume Heatmap — Day × Hour")

    dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = df.groupby(["dow", "hour"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(index=range(7), columns=range(24), fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=dow_labels,
        colorscale=[[0, "#0f172a"], [0.3, "#1e3a5f"], [0.7, "#1d4ed8"], [1, "#60a5fa"]],
        hovertemplate="Day: %{y}<br>Hour: %{x}<br>Tickets: %{z}<extra></extra>",
    ))
    layout = _plotly_layout(height=240)
    layout.update(margin=dict(l=60, r=20, t=20, b=60))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


# ── KB Articles Table ──────────────────────────────────────────────────────────

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


# ── Insight Cards ──────────────────────────────────────────────────────────────

def _render_insights(df: pd.DataFrame):
    st.markdown("#### Trend Insights")
    now = datetime.now(timezone.utc).date()

    # Last 7 days vs prior 7 days
    week1_start = now - timedelta(days=7)
    week2_start = now - timedelta(days=14)

    cur_week  = df[df["date"] >= week1_start]
    prev_week = df[(df["date"] >= week2_start) & (df["date"] < week1_start)]

    insights = []

    # Volume change
    if not prev_week.empty:
        change_pct = ((len(cur_week) - len(prev_week)) / len(prev_week) * 100)
        direction = "up" if change_pct >= 0 else "down"
        color     = "#ef4444" if change_pct > 10 else "#10b981" if change_pct < -5 else "#f59e0b"
        arrow     = "↑" if change_pct >= 0 else "↓"
        insights.append((f"{arrow} {abs(change_pct):.0f}% ticket volume {direction} this week", color))

    # Most common category this week
    if not cur_week.empty:
        top_cat = cur_week["cat"].value_counts().idxmax()
        top_pct = int(cur_week["cat"].value_counts().iloc[0] / len(cur_week) * 100)
        insights.append((f"📊 {top_cat} is top category this week ({top_pct}%)", "#60a5fa"))

    # Deflection rate this week
    if not cur_week.empty:
        week_defl = int((cur_week["status"] == "DEFLECTED").sum() / len(cur_week) * 100)
        color = "#10b981" if week_defl >= 15 else "#f59e0b"
        insights.append((f"🎯 {week_defl}% deflection rate this week", color))

    # P0/P1 count
    critical = cur_week[cur_week["urg"].isin(["P0", "P1"])]
    if not critical.empty:
        insights.append((f"🚨 {len(critical)} critical tickets (P0/P1) this week", "#ef4444"))

    # Angry sentiment
    angry = cur_week[cur_week["sent"] == "ANGRY"]
    if not angry.empty:
        angry_pct = int(len(angry) / len(cur_week) * 100) if len(cur_week) > 0 else 0
        color = "#ef4444" if angry_pct > 20 else "#f59e0b"
        insights.append((f"😡 {angry_pct}% of tickets are angry this week", color))

    for text, color in insights:
        st.markdown(f"""
        <div style='background:#0f172a; border-left:3px solid {color}; padding:0.6rem 0.8rem;
                    border-radius:0 6px 6px 0; margin-bottom:0.5rem;'>
            <span style='color:{color}; font-size:0.82rem; font-weight:500;'>{text}</span>
        </div>
        """, unsafe_allow_html=True)

    # ROI framing card
    stats = db.get_stats()
    hours_saved = round(stats["deflected"] * 0.5, 1)
    cost_saved  = round(hours_saved * 35, 0)  # $35/hr avg support cost
    st.markdown(f"""
    <div style='background:#022c22; border:1px solid #059669; border-radius:8px; padding:0.9rem; margin-top:0.75rem;'>
        <div style='color:#10b981; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.5rem;'>💰 ROI Estimate</div>
        <div style='color:#6ee7b7; font-size:0.82rem; line-height:1.5;'>
            <b>{stats['deflected']}</b> tickets deflected<br>
            ≈ <b>{hours_saved}h</b> agent time saved<br>
            ≈ <b>${cost_saved:,.0f}</b> in support costs
        </div>
        <div style='color:#047857; font-size:0.68rem; margin-top:6px;'>Based on $35/hr avg support cost · 0.5h avg handle time</div>
    </div>
    """, unsafe_allow_html=True)
