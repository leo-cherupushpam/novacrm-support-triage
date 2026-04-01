"""
Ticket Inbox — Agent view.
Filter bar, sortable ticket table, quick actions, Run AI Triage button.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import db
import classifier


# ── Helpers ───────────────────────────────────────────────────────────────────

URGENCY_BADGE = {
    "P0": '<span class="badge badge-p0">P0</span>',
    "P1": '<span class="badge badge-p1">P1</span>',
    "P2": '<span class="badge badge-p2">P2</span>',
    "P3": '<span class="badge badge-p3">P3</span>',
}
SENTIMENT_ICON = {
    "ANGRY": "😡",
    "FRUSTRATED": "😟",
    "NEUTRAL": "😐",
    "SATISFIED": "😊",
}
STATUS_BADGE = {
    "OPEN":        '<span class="status-open">Open</span>',
    "IN_PROGRESS": '<span class="status-in_progress">In Progress</span>',
    "RESOLVED":    '<span class="status-resolved">Resolved</span>',
    "DEFLECTED":   '<span class="status-deflected">Deflected</span>',
    "ESCALATED":   '<span class="status-escalated">Escalated</span>',
}

def _cat_badge(cat: str) -> str:
    cls = cat.replace(" ", "-") if cat else "Other"
    return f'<span class="cat-badge cat-{cls}">{cat or "Other"}</span>'

def _urgency(ticket: dict) -> str:
    return ticket.get("ai_urgency") or ticket.get("urgency") or "P3"

def _category(ticket: dict) -> str:
    return ticket.get("ai_category") or ticket.get("category") or "Other"

def _sentiment(ticket: dict) -> str:
    return ticket.get("ai_sentiment") or ticket.get("sentiment") or "NEUTRAL"

def _confidence(ticket: dict) -> float:
    return float(ticket.get("ai_confidence") or 0)

def _age(created_at: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:   return "< 1h"
        if hours < 24:  return f"{hours}h"
        return f"{hours // 24}d"
    except Exception:
        return "—"


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.markdown("## Ticket Inbox")
    st.markdown("<p style='color:#94a3b8; margin-top:-0.5rem; margin-bottom:1.5rem;'>Agent workspace · all incoming support tickets</p>", unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "OPEN", "IN_PROGRESS", "RESOLVED", "DEFLECTED", "ESCALATED"],
            )
        with col2:
            cat_filter = st.selectbox(
                "Category",
                ["All", "Billing", "Bug Report", "Integration", "Onboarding", "Account", "Feature Request", "Other"],
            )
        with col3:
            urgency_filter = st.selectbox(
                "Urgency",
                ["All", "P0", "P1", "P2", "P3"],
            )
        with col4:
            sort_by = st.selectbox(
                "Sort by",
                ["Newest first", "Oldest first", "Urgency (high→low)", "Confidence %"],
            )

    # ── Load tickets ─────────────────────────────────────────────────────────
    tickets = db.get_all_tickets(
        status=None if status_filter == "All" else status_filter,
        category=None if cat_filter == "All" else cat_filter,
        urgency=None if urgency_filter == "All" else urgency_filter,
    )

    # Sort
    urgency_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, None: 4}
    if sort_by == "Oldest first":
        tickets = list(reversed(tickets))
    elif sort_by == "Urgency (high→low)":
        tickets.sort(key=lambda t: urgency_order.get(_urgency(t), 4))
    elif sort_by == "Confidence %":
        tickets.sort(key=lambda t: _confidence(t), reverse=True)

    # ── Actions row ──────────────────────────────────────────────────────────
    col_count, col_triage, col_spacer = st.columns([2, 2, 6])
    with col_count:
        st.markdown(f"<div style='padding-top:0.5rem; color:#94a3b8; font-size:0.85rem;'>{len(tickets)} ticket{'s' if len(tickets) != 1 else ''}</div>", unsafe_allow_html=True)
    with col_triage:
        if st.button("⚡ Run AI Triage", type="primary"):
            _run_ai_triage()

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    if not tickets:
        st.info("No tickets match your filters.")
        return

    # ── Ticket table ─────────────────────────────────────────────────────────
    _render_ticket_table(tickets)


def _run_ai_triage():
    """Classify all OPEN tickets that have no AI classification yet."""
    unclassified = [
        t for t in db.get_all_tickets(status="OPEN")
        if not t.get("ai_category")
    ]
    if not unclassified:
        st.success("All open tickets are already classified!")
        return

    progress = st.progress(0, text=f"Classifying {len(unclassified)} tickets…")
    errors = 0
    for i, t in enumerate(unclassified):
        try:
            result = classifier.classify(t["subject"], t["body"])
            db.update_ticket(
                t["id"],
                ai_category=result["category"],
                ai_urgency=result["urgency"],
                ai_sentiment=result["sentiment"],
                ai_confidence=result["confidence"],
                ai_summary=result["summary"],
            )
            db.log_audit(t["id"], "AI Triage", "classified",
                         None, f'{result["category"]} · {result["urgency"]} · {result["sentiment"]}')
        except Exception:
            errors += 1
        progress.progress((i + 1) / len(unclassified),
                          text=f"Classified {i+1}/{len(unclassified)}…")

    progress.empty()
    if errors:
        st.warning(f"Classified {len(unclassified)-errors} tickets. {errors} failed.")
    else:
        st.success(f"✅ Classified {len(unclassified)} tickets. Refresh to see results.")


def _render_ticket_table(tickets: list[dict]):
    """Render tickets as a styled HTML table with click-to-select."""

    # Build header
    header = """
    <table style='width:100%; border-collapse:collapse; font-size:0.82rem;'>
    <thead>
    <tr style='border-bottom:1px solid #334155;'>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600; white-space:nowrap;'>ID</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Subject</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Customer</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Category</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Urgency</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Mood</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Confidence</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Status</th>
        <th style='padding:8px 12px; text-align:left; color:#64748b; font-weight:600;'>Age</th>
    </tr>
    </thead>
    <tbody>
    """

    rows = []
    for t in tickets:
        urg  = _urgency(t)
        cat  = _category(t)
        sent = _sentiment(t)
        conf = _confidence(t)
        status = t.get("status", "OPEN")

        conf_pct = f"{conf*100:.0f}%" if conf > 0 else "—"
        conf_color = "#10b981" if conf >= 0.8 else "#f59e0b" if conf >= 0.6 else "#94a3b8"

        subj = t["subject"]
        if len(subj) > 55:
            subj = subj[:55] + "…"

        assigned = t.get("assigned_to") or ""
        assigned_html = f"<div style='font-size:0.68rem; color:#64748b;'>{assigned}</div>" if assigned else ""

        rows.append(f"""
        <tr style='border-bottom:1px solid #1e293b; cursor:pointer;' onmouseover="this.style.background='#1e293b'" onmouseout="this.style.background='transparent'">
            <td style='padding:10px 12px; color:#475569; font-family:monospace;'>#{t['id']}</td>
            <td style='padding:10px 12px;'>
                <div style='color:#e2e8f0; font-weight:500;'>{subj}</div>
                {assigned_html}
            </td>
            <td style='padding:10px 12px;'>
                <div style='color:#cbd5e1;'>{t.get('customer_name','')}</div>
                <div style='font-size:0.68rem; color:#64748b;'>{t.get('customer_email','')[:28]}…</div>
            </td>
            <td style='padding:10px 12px;'>{_cat_badge(cat)}</td>
            <td style='padding:10px 12px;'>{URGENCY_BADGE.get(urg, urg)}</td>
            <td style='padding:10px 12px; text-align:center; font-size:1.1rem;'>{SENTIMENT_ICON.get(sent,'😐')}</td>
            <td style='padding:10px 12px; color:{conf_color}; font-weight:600;'>{conf_pct}</td>
            <td style='padding:10px 12px;'>{STATUS_BADGE.get(status, status)}</td>
            <td style='padding:10px 12px; color:#64748b; white-space:nowrap;'>{_age(t.get('created_at',''))}</td>
        </tr>
        """)

    html = header + "\n".join(rows) + "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Click-to-open selector ────────────────────────────────────────────────
    st.markdown("**Open a ticket:**")
    ticket_options = {f"#{t['id']} — {t['subject'][:60]}": t["id"] for t in tickets}
    selected_label = st.selectbox(
        "Select ticket to open",
        list(ticket_options.keys()),
        label_visibility="collapsed",
    )
    if selected_label and st.button("Open Ticket →", type="primary"):
        st.session_state["selected_ticket_id"] = ticket_options[selected_label]
        st.session_state["nav_to_detail"] = True
        st.rerun()

    # Handle navigation redirect
    if st.session_state.get("nav_to_detail"):
        st.session_state["nav_to_detail"] = False
        st.info("Navigate to **Ticket Detail** in the sidebar to view this ticket.")
