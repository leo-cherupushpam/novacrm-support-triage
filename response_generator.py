"""
AI draft response generator for support tickets.
Uses gpt-5-nano-2025-08-07 with relevant KB articles for context.
"""

from __future__ import annotations
import os
from typing import Optional


def _get_client():
    try:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY", "")
        return OpenAI(api_key=key) if key else None
    except ImportError:
        return None


def generate_response(subject: str, body: str, category: str,
                      kb_articles: list[dict], agent_name: str = "Support Team") -> str:
    """
    Generate a professional draft response for a support ticket.
    Falls back to a template if no API key is available.
    """
    client = _get_client()
    if not client:
        return _template_fallback(subject, category, agent_name)

    kb_context = "\n\n".join(
        f"KB Article: {a['title']}\n{a['content'][:400]}"
        for a in kb_articles[:3]
    ) if kb_articles else "No specific KB articles found."

    system = f"""You are a friendly, professional customer support agent for NovaCRM, a B2B CRM SaaS.
Write a helpful, empathetic draft response to the customer's support ticket.

Guidelines:
- Start with a warm greeting using their name if known
- Acknowledge their issue with empathy
- Provide a clear, actionable solution or next steps
- Reference the KB article content where relevant
- Close with next steps and offer for follow-up
- Keep it concise: 3-5 short paragraphs
- Sign off as "{agent_name}" from "NovaCRM Support"
- Do NOT promise specific timelines you can't guarantee
- Do NOT make up features that don't exist"""

    user = f"""Ticket Subject: {subject}
Customer Message: {body}
Category: {category}

Relevant Knowledge Base:
{kb_context}

Write the draft response:"""

    try:
        resp = _get_client().chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _template_fallback(subject, category, agent_name)


def _template_fallback(subject: str, category: str, agent_name: str) -> str:
    templates = {
        "Billing": (
            "Thank you for reaching out about your billing concern. "
            "I understand how important it is to have accurate billing information, and I'm sorry for any confusion this has caused.\n\n"
            "I've reviewed your account and will look into this right away. "
            "Could you please confirm your account email and the invoice number in question? "
            "This will help me resolve this as quickly as possible.\n\n"
            "I'll follow up within 1 business day with a full resolution. "
            "Thank you for your patience."
        ),
        "Bug Report": (
            "Thank you for reporting this issue. I'm sorry you're experiencing this — "
            "let's get it resolved as quickly as possible.\n\n"
            "To investigate further, could you please share: (1) the steps to reproduce the issue, "
            "(2) your browser and OS version, and (3) any error messages you're seeing?\n\n"
            "I've flagged this with our engineering team. In the meantime, "
            "try clearing your browser cache and logging in again — this resolves many display issues."
        ),
        "Integration": (
            "Thank you for reaching out about the integration issue. "
            "I understand how critical these connections are to your workflow.\n\n"
            "Please check that your API credentials are up to date in Settings → Integrations. "
            "If you recently rotated your API keys, you'll need to reconnect the integration. "
            "Our documentation at docs.novacrm.com/integrations has step-by-step guides.\n\n"
            "If the issue persists after trying these steps, please share a screenshot of any error messages "
            "and I'll escalate to our integrations team."
        ),
        "Onboarding": (
            "Welcome to NovaCRM! I'm happy to help you get set up.\n\n"
            "The fastest way to get started is through our onboarding checklist in your dashboard. "
            "We also have a dedicated setup guide at docs.novacrm.com/getting-started that walks through "
            "every step, including SSO configuration and team invites.\n\n"
            "Would it be helpful to schedule a 30-minute onboarding call? "
            "Our team is happy to walk you through the setup personally."
        ),
        "Account": (
            "Thank you for reaching out. Account and access issues are always a priority for us.\n\n"
            "For immediate help: if you're locked out, use the 'Forgot Password' link on the login page. "
            "For 2FA issues, your account admin can temporarily disable it under Settings → Security.\n\n"
            "If you need further assistance, please confirm your account email and I'll access your account "
            "directly to help resolve this."
        ),
    }
    body = templates.get(category, (
        "Thank you for contacting NovaCRM Support. I've received your request and will look into it right away.\n\n"
        "I'll follow up with a full response within 1 business day. "
        "In the meantime, our Help Center at docs.novacrm.com may have an immediate answer."
    ))
    return f"{body}\n\nBest regards,\n{agent_name}\nNovaCRM Support"
