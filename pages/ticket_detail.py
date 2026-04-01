"""
Ticket Detail — Single ticket deep-dive.
Left panel: ticket body + customer info.
Right panel: AI Suggestions (classification, KB articles, draft response, deflection).
"""

from __future__ import annotations
import streamlit as st
import db
import classifier
import response_generator
import deflection_engine


# ── Helpers ───────────────────────────────────────────────────────────────────

URGENCY_COLOR = {"P0": "#ef4444", "P1": "#f59e0b", "P2": "#eab308", "P3": "#22c55e"}
SENTIMENT_ICON = {"ANGRY": "😡", "FRUSTRATED": "😟", "NEUTRAL": "😐", "SATISFIED": "😊"}
SENTIMENT_COLOR = {"ANGRY": "#ef4444", "FRUSTRATED": "#f59e0b", "NEUTRAL": "#94a3b8", "SATISFIED": "#10b981"}


def _urgency(t): return t.get("ai_urgency") or t.get("urgency") or "P3"
def _category(t): return t.get("ai_category") or t.get("category") or "Other"
def _sentiment(t): return t.get("ai_sentiment") or t.get("sentiment") or "NEUTRAL"
def _confidence(t): return float(t.get("ai_confidence") or 0)


def _confidence_bar(score: float, label: str = "AI Confidence"):
    pct = int(score * 100)
    color = "#10b981" if score >= 0.8 else "#f59e0b" if score >= 0.6 else "#ef4444"
    st.markdown(f"""
    <div style='margin-bottom:0.75rem;'>
        <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#94a3b8; margin-bottom:4px;'>
            <span>{label}</span><span style='color:{color}; font-weight:700;'>{pct}%</span>
        </div>
        <div style='background:#334155; border-radius:4px; height:6px;'>
            <div style='background:{color}; width:{pct}%; height:6px; border-radius:4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _status_options():
    return ["OPEN", "IN_PROGRESS", "RESOLVED", "DEFLECTED", "ESCALATED"]


def _agent_list():
    return ["—", "Sarah Kim", "James Park", "Priya Nair", "Tom Walsh", "Ana Reyes"]


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.markdown("## Ticket Detail")

    # ── Ticket selector ───────────────────────────────────────────────────────
    all_tickets = db.get_all_tickets()
    if not all_tickets:
        st.info("No tickets found. Seed the database first.")
        return

    ticket_map = {f"#{t['id']} — {t['subject'][:55]}": t["id"] for t in all_tickets}

    # Pre-select from inbox navigation
    default_id = st.session_state.get("selected_ticket_id")
    default_label = None
    if default_id:
        default_label = next((k for k, v in ticket_map.items() if v == default_id), None)

    options = list(ticket_map.keys())
    default_idx = options.index(default_label) if default_label in options else 0

    selected_label = st.selectbox(
        "Select ticket",
        options,
        index=default_idx,
        label_visibility="collapsed",
    )

    ticket_id = ticket_map[selected_label]
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        st.error("Ticket not found.")
        return

    st.session_state["selected_ticket_id"] = ticket_id
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Two-panel layout ──────────────────────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        _render_left_panel(ticket)

    with right:
        _render_right_panel(ticket)

    # ── Audit trail ───────────────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    _render_audit(ticket_id)


def _render_left_panel(ticket: dict):
    urg = _urgency(ticket)
    cat = _category(ticket)
    sent = _sentiment(ticket)
    urg_color = URGENCY_COLOR.get(urg, "#94a3b8")
    sent_color = SENTIMENT_COLOR.get(sent, "#94a3b8")
    sent_icon  = SENTIMENT_ICON.get(sent, "😐")

    st.markdown(f"""
    <div style='background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.25rem; margin-bottom:1rem;'>
        <div style='display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:0.75rem;'>
            <div>
                <div style='font-size:1.1rem; font-weight:700; color:#f1f5f9; line-height:1.3;'>{ticket['subject']}</div>
                <div style='font-size:0.75rem; color:#64748b; margin-top:4px;'>Ticket #{ticket['id']} · {ticket.get('created_at','')[:10]}</div>
            </div>
            <div style='display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end;'>
                <span style='background:#1e293b; border:1px solid {urg_color}; color:{urg_color}; font-size:0.7rem; font-weight:700; padding:2px 8px; border-radius:4px;'>{urg}</span>
                <span style='font-size:1.1rem;' title='{sent}'>{sent_icon}</span>
            </div>
        </div>
        <div style='font-size:0.85rem; color:#94a3b8; line-height:1.6; white-space:pre-wrap;'>{ticket.get('body','')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Customer info
    st.markdown(f"""
    <div style='background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:1rem; margin-bottom:1rem;'>
        <div style='font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:0.5rem;'>Customer</div>
        <div style='color:#e2e8f0; font-weight:600; font-size:0.9rem;'>{ticket.get('customer_name','')}</div>
        <div style='color:#64748b; font-size:0.8rem;'>{ticket.get('customer_email','')}</div>
        {f"<div style='color:#94a3b8; font-size:0.75rem; margin-top:4px;'>Assigned to: {ticket.get('assigned_to','')}</div>" if ticket.get('assigned_to') else ""}
    </div>
    """, unsafe_allow_html=True)

    # AI Summary
    if ticket.get("ai_summary"):
        st.markdown(f"""
        <div style='background:#0f172a; border-left:3px solid #3b82f6; padding:0.75rem 1rem; border-radius:0 8px 8px 0; margin-bottom:1rem;'>
            <div style='font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#3b82f6; margin-bottom:4px;'>AI Summary</div>
            <div style='color:#cbd5e1; font-size:0.85rem; font-style:italic;'>{ticket.get('ai_summary','')}</div>
        </div>
        """, unsafe_allow_html=True)

    # Status + assignment controls
    st.markdown("**Update ticket**")
    col1, col2 = st.columns(2)
    with col1:
        new_status = st.selectbox(
            "Status",
            _status_options(),
            index=_status_options().index(ticket.get("status","OPEN")) if ticket.get("status","OPEN") in _status_options() else 0,
            key=f"status_{ticket['id']}",
        )
    with col2:
        agents = _agent_list()
        current_agent = ticket.get("assigned_to") or "—"
        agent_idx = agents.index(current_agent) if current_agent in agents else 0
        new_agent = st.selectbox(
            "Assign to",
            agents,
            index=agent_idx,
            key=f"agent_{ticket['id']}",
        )

    if st.button("Save changes", key=f"save_{ticket['id']}"):
        updates = {}
        if new_status != ticket.get("status"):
            updates["status"] = new_status
            if new_status == "RESOLVED":
                from datetime import datetime, timezone
                updates["resolved_at"] = datetime.now(timezone.utc).isoformat()
            db.log_audit(ticket["id"], "Agent", "status_change",
                         ticket.get("status"), new_status)
        if new_agent != (ticket.get("assigned_to") or "—"):
            updates["assigned_to"] = None if new_agent == "—" else new_agent
            db.log_audit(ticket["id"], "Agent", "assigned",
                         ticket.get("assigned_to"), new_agent)
        if updates:
            db.update_ticket(ticket["id"], **updates)
            st.success("Ticket updated!")
            st.rerun()
        else:
            st.info("No changes to save.")


def _render_right_panel(ticket: dict):
    st.markdown("""
    <div class='ai-panel'>
        <div class='ai-panel-title'>🤖 AI Suggestions Panel</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 1. Classification ──────────────────────────────────────────────────
    with st.expander("📊 Classification", expanded=True):
        if ticket.get("ai_category"):
            conf = _confidence(ticket)
            urg = _urgency(ticket)
            cat = _category(ticket)
            sent = _sentiment(ticket)
            urg_color = URGENCY_COLOR.get(urg, "#94a3b8")
            sent_color = SENTIMENT_COLOR.get(sent, "#94a3b8")

            col1, col2, col3 = st.columns(3)
            col1.metric("Category", cat)
            col2.metric("Urgency", urg)
            col3.metric("Sentiment", SENTIMENT_ICON.get(sent, "😐") + " " + sent.capitalize())

            _confidence_bar(conf)

            if st.button("🔄 Re-classify", key=f"reclassify_{ticket['id']}"):
                with st.spinner("Classifying…"):
                    result = classifier.classify(ticket["subject"], ticket["body"])
                    db.update_ticket(ticket["id"],
                        ai_category=result["category"],
                        ai_urgency=result["urgency"],
                        ai_sentiment=result["sentiment"],
                        ai_confidence=result["confidence"],
                        ai_summary=result["summary"],
                    )
                    db.log_audit(ticket["id"], "AI", "reclassified",
                                 cat, result["category"])
                st.success("Re-classified!")
                st.rerun()
        else:
            st.info("Not yet classified.")
            if st.button("⚡ Classify now", key=f"classify_{ticket['id']}"):
                with st.spinner("Classifying…"):
                    result = classifier.classify(ticket["subject"], ticket["body"])
                    db.update_ticket(ticket["id"],
                        ai_category=result["category"],
                        ai_urgency=result["urgency"],
                        ai_sentiment=result["sentiment"],
                        ai_confidence=result["confidence"],
                        ai_summary=result["summary"],
                    )
                    db.log_audit(ticket["id"], "AI", "classified", None, result["category"])
                st.success("Classified!")
                st.rerun()

    # ── 2. KB Article Matches ──────────────────────────────────────────────
    with st.expander("📚 Suggested KB Articles", expanded=True):
        cat = _category(ticket)
        matches = deflection_engine.find_matches(
            ticket["subject"], ticket["body"],
            category=cat if cat != "Other" else None,
            top_n=3,
        )
        relevant = [m for m in matches if m["score"] >= 0.05]

        if not relevant:
            st.caption("No relevant KB articles found.")
        else:
            for m in relevant:
                art = m["article"]
                score = m["score"]
                bar_w = int(score * 100)
                bar_color = "#10b981" if score >= 0.5 else "#f59e0b" if score >= 0.2 else "#64748b"
                st.markdown(f"""
                <div style='background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;'>
                    <div style='color:#e2e8f0; font-size:0.82rem; font-weight:600; margin-bottom:4px;'>{art['title']}</div>
                    <div style='font-size:0.72rem; color:#64748b; margin-bottom:6px;'>{art.get('category','')} · {art.get('tags','')}</div>
                    <div style='background:#1e293b; border-radius:3px; height:4px;'>
                        <div style='background:{bar_color}; width:{bar_w}%; height:4px; border-radius:3px;'></div>
                    </div>
                    <div style='text-align:right; font-size:0.68rem; color:{bar_color}; margin-top:3px;'>{bar_w}% relevance</div>
                </div>
                """, unsafe_allow_html=True)

        # Deflection suggestion
        defl = deflection_engine.check_deflection(
            ticket["id"], ticket["subject"], ticket["body"],
            category=cat if cat != "Other" else None,
        )
        if defl["can_deflect"]:
            st.markdown(f"""
            <div style='background:#022c22; border:1px solid #059669; border-radius:8px; padding:0.75rem; margin-top:0.5rem;'>
                <div style='color:#10b981; font-size:0.82rem; font-weight:700;'>✅ Deflectable</div>
                <div style='color:#6ee7b7; font-size:0.75rem; margin-top:4px;'>{defl['reason']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Mark as Deflected", key=f"deflect_{ticket['id']}"):
                db.update_ticket(ticket["id"], status="DEFLECTED")
                db.log_audit(ticket["id"], "AI", "auto_deflected", "OPEN", "DEFLECTED")
                st.success("Ticket marked as deflected!")
                st.rerun()

    # ── 3. AI Draft Response ───────────────────────────────────────────────
    with st.expander("✍️ AI Draft Response", expanded=True):
        existing_responses = db.get_ai_responses(ticket["id"])

        if existing_responses:
            draft = existing_responses[0]["draft_response"]
            model = existing_responses[0].get("model_used", "template")
            st.caption(f"Generated by: {model}")
        else:
            draft = None

        if draft:
            edited = st.text_area(
                "Draft response (editable):",
                value=draft,
                height=220,
                key=f"draft_{ticket['id']}",
                label_visibility="collapsed",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use this response", key=f"use_{ticket['id']}"):
                    if existing_responses:
                        db.mark_response_used(existing_responses[0]["id"])
                    db.update_ticket(ticket["id"], status="IN_PROGRESS")
                    db.log_audit(ticket["id"], "Agent", "response_used", None, "AI draft accepted")
                    st.success("Response marked as used!")
                    st.rerun()
            with col2:
                if st.button("🔄 Regenerate", key=f"regen_{ticket['id']}"):
                    _generate_draft(ticket)

        else:
            st.caption("No draft generated yet.")
            if st.button("✨ Generate draft", key=f"gen_{ticket['id']}"):
                _generate_draft(ticket)


def _generate_draft(ticket: dict):
    """Generate and save a new AI draft response."""
    cat = _category(ticket)
    matches = deflection_engine.find_matches(ticket["subject"], ticket["body"], category=cat, top_n=3)
    kb_arts = [m["article"] for m in matches if m["score"] >= 0.05]

    with st.spinner("Generating draft response…"):
        draft = response_generator.generate_response(
            subject=ticket["subject"],
            body=ticket["body"],
            category=cat,
            kb_articles=kb_arts,
            agent_name=ticket.get("assigned_to") or "Support Team",
        )
        model = "gpt-4o" if draft and "Best regards" not in draft[:30] else "template"
        response_id = db.add_ai_response(ticket["id"], draft, model=model)
        db.log_audit(ticket["id"], "AI", "draft_generated", None, f"Response #{response_id}")
    st.success("Draft generated!")
    st.rerun()


def _render_audit(ticket_id: int):
    audit = db.get_audit_log(ticket_id)
    if not audit:
        return

    st.markdown("### Audit Trail")
    for entry in audit[:10]:
        ts = entry.get("timestamp", "")[:16].replace("T", " ")
        action = entry.get("action", "")
        actor  = entry.get("changed_by", "")
        old    = entry.get("old_value") or ""
        new    = entry.get("new_value") or ""

        change = f"{old} → {new}" if old else new
        st.markdown(f"""
        <div style='display:flex; gap:1rem; font-size:0.78rem; padding:6px 0; border-bottom:1px solid #1e293b;'>
            <span style='color:#475569; min-width:120px;'>{ts}</span>
            <span style='color:#60a5fa; min-width:80px;'>{actor}</span>
            <span style='color:#94a3b8; min-width:120px;'>{action}</span>
            <span style='color:#cbd5e1;'>{change}</span>
        </div>
        """, unsafe_allow_html=True)
