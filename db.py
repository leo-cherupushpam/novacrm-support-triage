"""
Database layer for AI Support Triage.
SQLite with 5 tables: tickets, ai_responses, kb_articles, deflection_attempts, audit_log.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Any, Optional

DB_PATH = Path(__file__).parent / "support_triage.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables. Idempotent."""
    with _db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            subject         TEXT NOT NULL,
            body            TEXT NOT NULL,
            customer_name   TEXT NOT NULL,
            customer_email  TEXT NOT NULL,
            status          TEXT DEFAULT 'OPEN',
            category        TEXT,
            urgency         TEXT,
            sentiment       TEXT,
            ai_category     TEXT,
            ai_urgency      TEXT,
            ai_sentiment    TEXT,
            ai_confidence   REAL DEFAULT 0,
            ai_summary      TEXT,
            assigned_to     TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            resolved_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_responses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id       INTEGER NOT NULL,
            draft_response  TEXT NOT NULL,
            model_used      TEXT,
            was_used        INTEGER DEFAULT 0,
            agent_rating    INTEGER,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        CREATE TABLE IF NOT EXISTS kb_articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            category    TEXT NOT NULL,
            tags        TEXT,
            use_count   INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS deflection_attempts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id       INTEGER NOT NULL,
            kb_article_id   INTEGER,
            confidence      REAL,
            was_deflected   INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (ticket_id)     REFERENCES tickets(id),
            FOREIGN KEY (kb_article_id) REFERENCES kb_articles(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id   INTEGER,
            changed_by  TEXT NOT NULL,
            action      TEXT NOT NULL,
            old_value   TEXT,
            new_value   TEXT,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );
        """)


# ── Tickets ───────────────────────────────────────────────────────────────────

def create_ticket(subject: str, body: str, customer_name: str, customer_email: str,
                  category: str = None, urgency: str = None, sentiment: str = None,
                  ai_category: str = None, ai_urgency: str = None,
                  ai_sentiment: str = None, ai_confidence: float = 0,
                  ai_summary: str = None, status: str = "OPEN",
                  assigned_to: str = None, created_at: str = None) -> int:
    now = created_at or _now()
    with _db() as c:
        cur = c.execute("""
            INSERT INTO tickets
              (subject, body, customer_name, customer_email, status,
               category, urgency, sentiment,
               ai_category, ai_urgency, ai_sentiment, ai_confidence, ai_summary,
               assigned_to, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (subject, body, customer_name, customer_email, status,
              category, urgency, sentiment,
              ai_category, ai_urgency, ai_sentiment, ai_confidence, ai_summary,
              assigned_to, now, now))
        return cur.lastrowid


def get_ticket(ticket_id: int) -> Optional[dict]:
    with _db() as c:
        row = c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        return dict(row) if row else None


def get_all_tickets(status: str = None, category: str = None,
                    urgency: str = None) -> list[dict]:
    sql = "SELECT * FROM tickets WHERE 1=1"
    params: list[Any] = []
    if status:    sql += " AND status=?";   params.append(status)
    if category:  sql += " AND (category=? OR ai_category=?)"; params += [category, category]
    if urgency:   sql += " AND (urgency=? OR ai_urgency=?)";   params += [urgency, urgency]
    sql += " ORDER BY created_at DESC"
    with _db() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def update_ticket(ticket_id: int, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = _now()
    cols = ", ".join(f"{k}=?" for k in fields)
    with _db() as c:
        c.execute(f"UPDATE tickets SET {cols} WHERE id=?",
                  list(fields.values()) + [ticket_id])


# ── AI Responses ──────────────────────────────────────────────────────────────

def add_ai_response(ticket_id: int, draft: str, model: str = "gpt-4o") -> int:
    with _db() as c:
        cur = c.execute("""
            INSERT INTO ai_responses (ticket_id, draft_response, model_used, created_at)
            VALUES (?,?,?,?)
        """, (ticket_id, draft, model, _now()))
        return cur.lastrowid


def get_ai_responses(ticket_id: int) -> list[dict]:
    with _db() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM ai_responses WHERE ticket_id=? ORDER BY created_at DESC",
            (ticket_id,)).fetchall()]


def mark_response_used(response_id: int, rating: int = None) -> None:
    with _db() as c:
        c.execute("UPDATE ai_responses SET was_used=1, agent_rating=? WHERE id=?",
                  (rating, response_id))


# ── KB Articles ───────────────────────────────────────────────────────────────

def create_kb_article(title: str, content: str, category: str, tags: str = "") -> int:
    with _db() as c:
        cur = c.execute("""
            INSERT INTO kb_articles (title, content, category, tags, created_at)
            VALUES (?,?,?,?,?)
        """, (title, content, category, tags, _now()))
        return cur.lastrowid


def get_kb_articles(category: str = None) -> list[dict]:
    sql = "SELECT * FROM kb_articles"
    params = []
    if category:
        sql += " WHERE category=?"
        params.append(category)
    sql += " ORDER BY use_count DESC"
    with _db() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def increment_kb_use(article_id: int) -> None:
    with _db() as c:
        c.execute("UPDATE kb_articles SET use_count=use_count+1 WHERE id=?", (article_id,))


# ── Deflection ────────────────────────────────────────────────────────────────

def log_deflection(ticket_id: int, kb_article_id: Optional[int],
                   confidence: float, was_deflected: bool) -> None:
    with _db() as c:
        c.execute("""
            INSERT INTO deflection_attempts
              (ticket_id, kb_article_id, confidence, was_deflected, created_at)
            VALUES (?,?,?,?,?)
        """, (ticket_id, kb_article_id, confidence, int(was_deflected), _now()))


# ── Audit Log ─────────────────────────────────────────────────────────────────

def log_audit(ticket_id: Optional[int], changed_by: str, action: str,
              old_value: str = None, new_value: str = None) -> None:
    with _db() as c:
        c.execute("""
            INSERT INTO audit_log (ticket_id, changed_by, action, old_value, new_value, timestamp)
            VALUES (?,?,?,?,?,?)
        """, (ticket_id, changed_by, action, old_value, new_value, _now()))


def get_audit_log(ticket_id: int) -> list[dict]:
    with _db() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM audit_log WHERE ticket_id=? ORDER BY timestamp DESC",
            (ticket_id,)).fetchall()]


# ── Analytics helpers ─────────────────────────────────────────────────────────

def get_stats() -> dict:
    with _db() as c:
        total      = c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        open_count = c.execute("SELECT COUNT(*) FROM tickets WHERE status='OPEN'").fetchone()[0]
        deflected  = c.execute("SELECT COUNT(*) FROM tickets WHERE status='DEFLECTED'").fetchone()[0]
        p0_open    = c.execute("SELECT COUNT(*) FROM tickets WHERE status='OPEN' AND (urgency='P0' OR ai_urgency='P0')").fetchone()[0]
        resolved   = c.execute("SELECT COUNT(*) FROM tickets WHERE status='RESOLVED'").fetchone()[0]
        escalated  = c.execute("SELECT COUNT(*) FROM tickets WHERE status='ESCALATED'").fetchone()[0]
    deflection_rate = round(deflected / total * 100, 1) if total else 0
    return {
        "total": total, "open": open_count, "deflected": deflected,
        "resolved": resolved, "escalated": escalated,
        "p0_open": p0_open, "deflection_rate": deflection_rate,
    }


def clear_all() -> None:
    with _db() as c:
        for t in ("audit_log","deflection_attempts","ai_responses","tickets","kb_articles"):
            c.execute(f"DELETE FROM {t}")
