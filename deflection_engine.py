"""
Deflection engine — determines if a ticket can be auto-answered by a KB article.
Uses keyword overlap + category matching. No embeddings required.
"""

from __future__ import annotations
import re
import db


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\b\w{3,}\b', text.lower()))


def score_article(ticket_text: str, article: dict) -> float:
    """Score relevance of a KB article to ticket text (0–1)."""
    ticket_tokens = _tokenize(ticket_text)
    article_tokens = _tokenize(article["title"] + " " + article["content"])

    # Tag bonus
    tags = set(t.strip().lower() for t in (article.get("tags") or "").split(",") if t.strip())
    tag_hits = len(tags & ticket_tokens)

    # Token overlap (Jaccard-style)
    intersection = ticket_tokens & article_tokens
    union = ticket_tokens | article_tokens
    jaccard = len(intersection) / len(union) if union else 0

    # Boost for tag hits
    score = min(1.0, jaccard * 3 + tag_hits * 0.08)
    return round(score, 3)


def find_matches(ticket_subject: str, ticket_body: str,
                 category: str = None, top_n: int = 3) -> list[dict]:
    """
    Return top-N KB articles sorted by relevance score.
    Each item: {article, score}
    """
    ticket_text = ticket_subject + " " + ticket_body
    articles = db.get_kb_articles(category=category) or db.get_kb_articles()

    scored = [
        {"article": a, "score": score_article(ticket_text, a)}
        for a in articles
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def check_deflection(ticket_id: int, subject: str, body: str,
                     category: str = None, threshold: float = 0.85) -> dict:
    """
    Check whether a ticket can be deflected by a KB article.
    Returns: {can_deflect, article, confidence, reason}
    Logs the attempt to the database.
    """
    matches = find_matches(subject, body, category, top_n=1)

    if not matches or matches[0]["score"] < 0.10:
        db.log_deflection(ticket_id, None, 0.0, False)
        return {"can_deflect": False, "article": None, "confidence": 0.0,
                "reason": "No relevant KB article found"}

    best = matches[0]
    score = best["score"]
    article = best["article"]
    can_deflect = score >= threshold

    db.log_deflection(ticket_id, article["id"], score, can_deflect)
    if can_deflect:
        db.increment_kb_use(article["id"])

    return {
        "can_deflect": can_deflect,
        "article": article,
        "confidence": score,
        "reason": (
            f"KB article '{article['title']}' matches with {score*100:.0f}% confidence"
            if can_deflect
            else f"Best match ({score*100:.0f}%) below deflection threshold ({threshold*100:.0f}%)"
        ),
    }
