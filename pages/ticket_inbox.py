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

    # ── Quick Stats ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        urgent = len([t for t in tickets if _urgency(t) in ["P0", "P1"]])
        col1.metric("Urgent (P0+P1)", urgent, delta=None)
    with col2:
        open_count = len([t for t in tickets if t.get("status") == "OPEN"])
        col2.metric("Unassigned", open_count, delta=None)
    with col3:
        angry = len([t for t in tickets if _sentiment(t) == "ANGRY"])
        col3.metric("Angry Sentiment", angry, delta=None)
    with col4:
        avg_conf = sum(_confidence(t) for t in tickets) / len(tickets) if tickets else 0
        col4.metric("Avg AI Confidence", f"{avg_conf*100:.0f}%", delta=None)

    st.markdown("<br>", unsafe_allow_html=True)

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
    """Render tickets as a native Streamlit dataframe."""

    # Build dataframe
    rows_data = []
    for t in tickets:
        urg  = _urgency(t)
        cat  = _category(t)
        sent = _sentiment(t)
        conf = _confidence(t)
        status = t.get("status", "OPEN")

        conf_pct = f"{conf*100:.0f}%" if conf > 0 else "—"
        subj = t["subject"]
        if len(subj) > 55:
            subj = subj[:55] + "…"

        rows_data.append({
            "ID": t["id"],
            "Subject": subj,
            "Customer": t.get("customer_name", ""),
            "Category": cat,
            "Urgency": urg,
            "Mood": SENTIMENT_ICON.get(sent, "😐"),
            "Confidence": conf_pct,
            "Status": status,
            "Age": _age(t.get("created_at", "")),
        })

    df = pd.DataFrame(rows_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=max(300, min(len(rows_data) * 35 + 40, 600)),
    )

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
