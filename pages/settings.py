"""
Settings — Configuration page.
KB article manager, categories, deflection threshold, agent roster, data reset.
"""

from __future__ import annotations
import streamlit as st
import db


def render():
    st.markdown("## Settings")
    st.markdown("<p style='color:#94a3b8; margin-top:-0.5rem; margin-bottom:1.5rem;'>System configuration · KB articles · agent roster</p>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📚 KB Articles", "⚙️ Triage Config", "👥 Agent Roster", "🗄️ Data"])

    with tab1:
        _tab_kb_articles()
    with tab2:
        _tab_config()
    with tab3:
        _tab_agents()
    with tab4:
        _tab_data()


# ── KB Articles ────────────────────────────────────────────────────────────────

def _tab_kb_articles():
    st.markdown("### Knowledge Base Articles")
    st.caption("These articles power the AI deflection engine. Higher-quality articles improve deflection rates.")

    articles = db.get_kb_articles()

    # Stats row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", len(articles))
    col2.metric("Total Uses", sum(a.get("use_count", 0) for a in articles))
    cats = list({a["category"] for a in articles})
    col3.metric("Categories Covered", len(cats))

    st.markdown("---")

    # Article list
    if articles:
        for art in articles:
            with st.expander(f"#{art['id']} · {art['title']} — {art['category']} ({art.get('use_count',0)} uses)"):
                st.markdown(f"**Category:** {art['category']}")
                st.markdown(f"**Tags:** `{art.get('tags','')}`")
                st.markdown(f"**Uses:** {art.get('use_count',0)}")
                st.markdown("**Content:**")
                st.text_area(
                    "Content",
                    value=art["content"],
                    height=120,
                    key=f"art_content_{art['id']}",
                    disabled=True,
                    label_visibility="collapsed",
                )
    else:
        st.info("No KB articles yet.")

    st.markdown("---")
    st.markdown("### Add New KB Article")

    with st.form("add_kb"):
        title = st.text_input("Title *")
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Category *",
                ["Billing", "Bug Report", "Integration", "Onboarding", "Account", "Feature Request", "Other"],
            )
        with col2:
            tags = st.text_input("Tags (comma-separated)", placeholder="password, login, 2fa")

        content = st.text_area("Content *", height=150, placeholder="Write the KB article content here…")

        if st.form_submit_button("➕ Add Article", type="primary"):
            if title and content:
                art_id = db.create_kb_article(title=title, content=content, category=category, tags=tags)
                st.success(f"✅ Article #{art_id} created!")
                st.rerun()
            else:
                st.error("Title and content are required.")


# ── Triage Config ──────────────────────────────────────────────────────────────

def _tab_config():
    st.markdown("### Triage Configuration")

    # Deflection threshold
    st.markdown("#### Auto-Deflection Threshold")
    st.caption("Tickets with a KB article match above this threshold will be suggested for deflection.")

    threshold = st.slider(
        "Confidence threshold",
        min_value=0.50,
        max_value=0.99,
        value=st.session_state.get("deflection_threshold", 0.85),
        step=0.01,
        format="%.2f",
        key="threshold_slider",
    )
    st.session_state["deflection_threshold"] = threshold

    low, med, high = 0.70, 0.80, 0.90
    if threshold >= high:
        st.success(f"✅ Conservative: only very high-confidence matches ({threshold*100:.0f}%+) will be deflected. Fewer auto-deflections, higher accuracy.")
    elif threshold >= med:
        st.info(f"ℹ️ Balanced: good precision/recall tradeoff at {threshold*100:.0f}%.")
    else:
        st.warning(f"⚠️ Aggressive: lower threshold ({threshold*100:.0f}%) may cause false deflections. Monitor closely.")

    st.markdown("---")

    # Category management
    st.markdown("#### Categories")
    categories = ["Billing", "Bug Report", "Integration", "Onboarding", "Account", "Feature Request", "Other"]
    st.caption("These are the standard ticket categories used by the AI classifier.")

    for cat in categories:
        count = len(db.get_all_tickets(category=cat))
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center;
                    padding:8px 12px; background:#1e293b; border-radius:6px; margin-bottom:4px;'>
            <span style='color:#e2e8f0; font-size:0.85rem;'>{cat}</span>
            <span style='color:#64748b; font-size:0.78rem;'>{count} tickets</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Response templates info
    st.markdown("#### Response Templates")
    st.caption("Fallback templates are used when no OpenAI API key is configured.")
    template_cats = ["Billing", "Bug Report", "Integration", "Onboarding", "Account"]
    for cat in template_cats:
        st.markdown(f"✅ **{cat}** — template configured")
    st.info("To use AI-powered responses, set `OPENAI_API_KEY` in your environment or `.env` file.")


# ── Agent Roster ───────────────────────────────────────────────────────────────

def _tab_agents():
    st.markdown("### Agent Roster")
    st.caption("Support agents available for ticket assignment.")

    agents = [
        {"name": "Sarah Kim",  "email": "sarah.kim@novacrm.com",   "role": "Senior Agent",   "active": True},
        {"name": "James Park", "email": "james.park@novacrm.com",  "role": "Agent",           "active": True},
        {"name": "Priya Nair", "email": "priya.nair@novacrm.com",  "role": "Team Lead",       "active": True},
        {"name": "Tom Walsh",  "email": "tom.walsh@novacrm.com",   "role": "Agent",           "active": True},
        {"name": "Ana Reyes",  "email": "ana.reyes@novacrm.com",   "role": "Agent",           "active": False},
    ]

    for agent in agents:
        status_color = "#10b981" if agent["active"] else "#64748b"
        status_label = "Active" if agent["active"] else "Inactive"
        tickets_assigned = len([t for t in db.get_all_tickets() if t.get("assigned_to") == agent["name"]])

        st.markdown(f"""
        <div style='background:#1e293b; border:1px solid #334155; border-radius:8px;
                    padding:0.75rem 1rem; margin-bottom:0.5rem;
                    display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <div style='color:#f1f5f9; font-weight:600; font-size:0.9rem;'>{agent['name']}</div>
                <div style='color:#64748b; font-size:0.75rem;'>{agent['email']} · {agent['role']}</div>
            </div>
            <div style='text-align:right;'>
                <div style='color:{status_color}; font-size:0.75rem; font-weight:600;'>● {status_label}</div>
                <div style='color:#64748b; font-size:0.72rem;'>{tickets_assigned} tickets assigned</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info("Agent roster is currently read-only. In production, this would sync with your identity provider.")


# ── Data Management ────────────────────────────────────────────────────────────

def _tab_data():
    st.markdown("### Data Management")

    stats = db.get_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", stats["total"])
    col2.metric("KB Articles", len(db.get_kb_articles()))
    col3.metric("Deflection Attempts", stats["deflected"])

    st.markdown("---")

    st.markdown("#### Re-seed Demo Data")
    st.caption("Clears all data and reloads the 60 pre-built demo tickets + 15 KB articles.")
    if st.button("🌱 Re-seed database", type="secondary"):
        st.session_state["confirm_reseed"] = True

    if st.session_state.get("confirm_reseed"):
        st.warning("This will delete all current data. Are you sure?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Yes, re-seed", type="primary"):
                with st.spinner("Seeding…"):
                    import seed_data
                    seed_data.seed()
                st.success("✅ Database re-seeded with demo data!")
                st.session_state["confirm_reseed"] = False
                st.rerun()
        with col_no:
            if st.button("❌ Cancel"):
                st.session_state["confirm_reseed"] = False
                st.rerun()

    st.markdown("---")
    st.markdown("#### Export Data")
    st.caption("Download tickets as CSV for offline analysis.")

    tickets = db.get_all_tickets()
    if tickets:
        import pandas as pd
        import io
        df = pd.DataFrame(tickets)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇️ Download tickets.csv",
            data=csv_buf.getvalue(),
            file_name="novacrm_tickets.csv",
            mime="text/csv",
        )
