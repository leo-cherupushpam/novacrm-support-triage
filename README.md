# NovaCRM AI Support Triage

**AI-powered customer support triage system for enterprise SaaS — automatically classifies tickets, surfaces relevant KB articles, generates draft responses, and tracks deflection ROI.**

🔗 **[Live Demo](https://novacrm-support-triage.streamlit.app)** · Built with Streamlit + OpenAI GPT-4o

---

## The Problem

Enterprise SaaS support teams waste 40–60% of agent time on repetitive, answerable tickets. Without intelligent routing, P0 incidents get buried in billing noise, new agents write inconsistent responses, and managers have no visibility into deflection rates or SLA compliance.

## The Solution

NovaCRM Support Triage is an AI-powered triage layer that:

| Capability | How it works |
|---|---|
| **Smart Classification** | GPT-4o-mini classifies every ticket into category, urgency (P0–P3), and sentiment in < 1s |
| **KB Deflection Engine** | Jaccard + tag-weighted scoring matches tickets to KB articles; suggests auto-deflection at configurable confidence thresholds |
| **AI Draft Responses** | GPT-4o generates contextual draft replies grounded in your KB content — agents review and send, never auto-send |
| **Manager Analytics** | Deflection rates, volume trends, SLA breach tracking, ROI estimation |
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
| LLM — Classification | OpenAI `gpt-4o-mini` (fast, cost-efficient) |
| LLM — Response Gen | OpenAI `gpt-4o` |
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
- Color-coded urgency badges (P0=red → P3=green)
- Sentiment icons (😡 😟 😐 😊) at a glance
- AI Confidence % for each classification
- One-click "Run AI Triage" to batch-classify all open tickets

### Ticket Detail (Agent View)
- Full ticket body + customer info
- AI suggestions panel (right side):
  - Classification result with confidence bar
  - Top 3 KB article matches with relevance scores
  - Deflection suggestion when confidence > threshold
  - Editable AI draft response with regenerate option
- Status updates and agent assignment
- Full audit trail

### Analytics Dashboard (Manager View)
- Ticket volume trend with deflection rate overlay
- Category donut chart + urgency/sentiment breakdowns
- Day × Hour heatmap (identify peak support times)
- Top KB articles by usage count
- Automated trend insight cards
- ROI estimate card

### Settings
- KB article manager (view, add articles)
- Deflection threshold slider with recommendation text
- Agent roster
- One-click database re-seed + CSV export

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
