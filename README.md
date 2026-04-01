# NovaCRM AI Support Triage

**AI-powered customer support triage system for enterprise SaaS — automatically classifies tickets, surfaces relevant KB articles, generates draft responses, and tracks deflection ROI.**

🔗 **[Live Demo](https://novacrm-support-triage.streamlit.app)** · Built with Streamlit + OpenAI GPT-5

---

## The Problem

Enterprise SaaS support teams waste 40–60% of agent time on repetitive, answerable tickets. Without intelligent routing, P0 incidents get buried in billing noise, new agents write inconsistent responses, and managers have no visibility into deflection rates or SLA compliance.

## The Solution

NovaCRM Support Triage is an AI-powered triage layer that:

| Capability | How it works |
|---|---|
| **Smart Classification** | GPT-5-nano classifies every ticket into category, urgency (P0–P3), and sentiment in < 1s |
| **KB Deflection Engine** | Jaccard + tag-weighted scoring matches tickets to KB articles; suggests auto-deflection at configurable confidence thresholds |
| **AI Draft Responses** | GPT-5-nano generates contextual draft replies grounded in your KB content — agents review and send, never auto-send |
| **Agent Workflow** | Quick action buttons (Start Work, Resolve, Escalate) for fast ticket handling; AI suggestions panel with KB matches and draft responses |
| **Manager Analytics** | Deflection rates, response times, SLA targets, trend insights, ROI estimation with 5-metric dashboard |
| **Graceful Degradation** | Full demo works without any API key; rule-based fallbacks ensure zero downtime |

---

## ROI Framing

```
10 deflected tickets/day × 0.5h avg handle time × $35/hr = $175/day saved
= $63,875/year per support team
```

Deflection rate visible live on the analytics dashboard.

---

## Architecture

```
app.py                    ← Streamlit entry point, KPI header, routing
├── db.py                 ← SQLite (5 tables: tickets, ai_responses, kb_articles,
│                             deflection_attempts, audit_log)
├── classifier.py         ← GPT-4o-mini structured JSON classification
├── response_generator.py ← GPT-4o contextual draft responses
├── deflection_engine.py  ← Jaccard KB matching, configurable threshold
├── seed_data.py          ← 60 pre-classified tickets + 15 KB articles
└── pages/
    ├── ticket_inbox.py   ← Agent: filter bar, urgency badges, sentiment icons
    ├── ticket_detail.py  ← Agent: full ticket + AI suggestions panel (60/40)
    ├── analytics.py      ← Manager: 6 charts + ROI estimate + insight cards
    └── settings.py       ← KB manager, deflection threshold, agent roster
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Streamlit |
| LLM — Classification | OpenAI `gpt-5-nano-2025-08-07` (fast, cost-efficient) |
| LLM — Response Gen | OpenAI `gpt-5-nano-2025-08-07` |
| Database | SQLite (WAL mode) |
| Charts | Plotly |
| Demo data | Pre-seeded SQLite via `seed_data.py` |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/leo-cherupushpam/novacrm-support-triage.git
cd novacrm-support-triage

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Add OpenAI key for live AI features
cp .env.example .env
echo "OPENAI_API_KEY=sk-..." >> .env

# 4. Seed demo data
python seed_data.py

# 5. Run
streamlit run app.py
```

The app works fully without an API key — all 60 tickets are pre-classified using realistic seed data.

---

## Key Features

### Ticket Inbox (Agent View)
- Filter by status, category, urgency, and assignee
- Quick stats: Urgent count, unassigned tickets, angry sentiment, AI confidence average
- Color-coded urgency badges (P0=red → P3=green)
- Sentiment icons (😡 😟 😐 😊) at a glance
- AI Confidence % for each classification
- Sortable table view with customer context
- One-click "Run AI Triage" to batch-classify all open tickets

### Ticket Detail (Agent View)
- Full ticket body + customer info + AI summary
- Quick action buttons (Start Work, Resolve, Escalate) for fast ticket handling
- AI suggestions panel (right side):
  - Classification result with confidence bar
  - Top 3 KB article matches with relevance scores
  - Deflection suggestion when confidence > threshold
  - Editable AI draft response with regenerate option
  - One-click "Use this response" to accept AI draft
- Status updates and agent assignment
- Full audit trail with actor, timestamp, and change tracking

### Analytics Dashboard (Manager View)
- KPI Cards: Total Tickets, Deflection Rate, Open Tickets, Resolved, P0 Open
- Response time metrics: Average first response time with SLA tracking
- Category breakdown bar chart
- Urgency distribution with color coding
- Sentiment analysis (angry, frustrated, neutral, satisfied)
- Status breakdown pie chart
- Trend insights: Top category, angry sentiment count, critical P0 tickets
- ROI estimate with deflection multiplier ($35/hr, 0.5h avg)
- Top KB articles by usage count

### Settings
- KB article manager (view, add articles, track usage)
- Deflection threshold slider (50%–99%) with conservative/balanced/aggressive recommendations
- Response time SLA configuration (P0/P1/P3 targets)
- Agent roster with active status and assignment count
- One-click database re-seed + CSV export for offline analysis

---

## Design Principles

1. **Confidence-gated automation** — AI never acts autonomously; every suggestion requires agent confirmation
2. **Graceful degradation** — rule-based fallbacks ensure the product works without API access
3. **Dual persona design** — agents get workflow efficiency; managers get business metrics
4. **Audit trail** — every AI classification, override, and status change is logged
5. **ROI transparency** — deflection savings are quantified and visible on the dashboard

---

## Roadmap

- [ ] Slack/email integration for ticket ingestion
- [ ] Vector embedding-based KB search (replace Jaccard with semantic similarity)
- [ ] SLA breach alerts (webhook + email)
- [ ] Agent performance metrics
- [ ] Multi-tenant support with per-org KB articles
- [ ] CSAT survey automation post-resolution
