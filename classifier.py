"""
LLM-based ticket classifier using OpenAI gpt-4o-mini.
Returns category, urgency, sentiment, confidence, and a one-line summary.
Falls back gracefully when no API key is present.
"""

from __future__ import annotations
import json
import os
from typing import Optional

_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            from openai import OpenAI
            key = os.getenv("OPENAI_API_KEY", "")
            if key:
                _client = OpenAI(api_key=key)
        except ImportError:
            pass
    return _client


SYSTEM_PROMPT = """You are a customer support triage AI for NovaCRM, a B2B SaaS CRM platform.
Classify the support ticket below and return ONLY valid JSON with these exact fields:

{
  "category": one of ["Billing", "Bug Report", "Integration", "Onboarding", "Account", "Feature Request", "Other"],
  "urgency": one of ["P0", "P1", "P2", "P3"],
  "sentiment": one of ["ANGRY", "FRUSTRATED", "NEUTRAL", "SATISFIED"],
  "confidence": float between 0.0 and 1.0,
  "summary": "one sentence describing the core issue"
}

Urgency guide:
- P0: Production down, data loss, security breach — needs immediate response
- P1: Major feature broken, significant business impact — same day response
- P2: Feature partially broken or degraded — next business day
- P3: Question, minor issue, feature request — standard SLA"""


def classify(subject: str, body: str) -> dict:
    """
    Classify a ticket using gpt-4o-mini.
    Returns classification dict. Falls back to rule-based if no API key.
    """
    client = _get_client()
    if not client:
        return _rule_based_fallback(subject, body)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Subject: {subject}\n\nBody: {body}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=200,
        )
        result = json.loads(resp.choices[0].message.content)
        # Validate required fields
        for field in ("category", "urgency", "sentiment", "confidence", "summary"):
            if field not in result:
                raise ValueError(f"Missing field: {field}")
        return result
    except Exception:
        return _rule_based_fallback(subject, body)


def _rule_based_fallback(subject: str, body: str) -> dict:
    """Simple keyword-based fallback when OpenAI is unavailable."""
    text = (subject + " " + body).lower()

    # Category
    if any(w in text for w in ("invoice", "billing", "charge", "payment", "subscription", "refund", "price")):
        category = "Billing"
    elif any(w in text for w in ("error", "bug", "broken", "crash", "fail", "not working", "issue")):
        category = "Bug Report"
    elif any(w in text for w in ("salesforce", "slack", "zapier", "integration", "api", "webhook", "sync")):
        category = "Integration"
    elif any(w in text for w in ("setup", "onboard", "getting started", "how to", "configure", "sso", "invite")):
        category = "Onboarding"
    elif any(w in text for w in ("password", "login", "account", "2fa", "seat", "user", "access")):
        category = "Account"
    elif any(w in text for w in ("feature", "request", "would be great", "suggestion", "roadmap")):
        category = "Feature Request"
    else:
        category = "Other"

    # Urgency
    if any(w in text for w in ("urgent", "critical", "down", "outage", "data loss", "emergency")):
        urgency = "P0"
    elif any(w in text for w in ("broken", "not working", "blocked", "asap", "major")):
        urgency = "P1"
    elif any(w in text for w in ("slow", "intermittent", "sometimes", "occasionally")):
        urgency = "P2"
    else:
        urgency = "P3"

    # Sentiment
    if any(w in text for w in ("furious", "terrible", "awful", "unacceptable", "ridiculous", "cancel")):
        sentiment = "ANGRY"
    elif any(w in text for w in ("frustrated", "disappointed", "annoying", "confusing", "problem")):
        sentiment = "FRUSTRATED"
    elif any(w in text for w in ("great", "thanks", "helpful", "appreciate", "love")):
        sentiment = "SATISFIED"
    else:
        sentiment = "NEUTRAL"

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "confidence": 0.72,
        "summary": f"Customer reports a {category.lower()} issue: {subject[:80]}",
    }
