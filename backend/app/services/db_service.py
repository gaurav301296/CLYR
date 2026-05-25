"""
CLYR Database Service
SQLite-based persistence for reports, orders, waitlist, DSA leads.
Single shared DB with WAL mode for concurrent reads.
"""
import os
import sqlite3
import json
import time
import logging
import secrets
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = None

def _get_db_path():
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = os.environ.get("CLYR_DB_PATH", str(Path(__file__).parent.parent.parent / "clyr.db"))
    return DB_PATH


def get_db():
    """Get SQLite connection with WAL mode."""
    db = sqlite3.connect(_get_db_path(), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    # Note: foreign_keys pragma removed — FK constraints removed from schema
    # for MVP simplicity. Application-level integrity enforcement.
    db.execute("PRAGMA busy_timeout=5000")
    return db


def init_db():
    """Initialize all database tables."""
    db = get_db()
    db.executescript("""
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        -- Refresh tokens
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at REAL NOT NULL,
            created_at REAL NOT NULL
        );

        -- Credit reports (generated from PDF upload)
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            customer_name TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            letter_text TEXT DEFAULT '',
            issues_json TEXT DEFAULT '[]',
            action_steps_json TEXT DEFAULT '[]',
            timeline_json TEXT DEFAULT '[]',
            general_health TEXT DEFAULT '',
            status TEXT DEFAULT 'completed',
            pdf_url TEXT DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        -- Payment orders
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            report_id TEXT,
            plan TEXT NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT DEFAULT 'INR',
            razorpay_order_id TEXT DEFAULT '',
            razorpay_payment_id TEXT DEFAULT '',
            razorpay_signature TEXT DEFAULT '',
            status TEXT DEFAULT 'created',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        -- Waitlist entries
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'landing_page',
            converted INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        );

        -- DSA leads
        CREATE TABLE IF NOT EXISTS dsa_leads (
            id TEXT PRIMARY KEY,
            dsa_user_id TEXT NOT NULL,
            client_name TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'Starter',
            status TEXT DEFAULT 'Actioned',
            commission INTEGER DEFAULT 100,
            created_at REAL NOT NULL
        );

        -- DSA referral codes
        CREATE TABLE IF NOT EXISTS dsa_referrals (
            user_id TEXT PRIMARY KEY,
            referral_code TEXT UNIQUE NOT NULL,
            referral_link TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        -- Security audit log
        CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT DEFAULT '',
            details TEXT DEFAULT '',
            created_at REAL NOT NULL
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
        CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist(email);
        CREATE INDEX IF NOT EXISTS idx_dsa_leads_user ON dsa_leads(dsa_user_id);
        CREATE INDEX IF NOT EXISTS idx_dsa_referrals_code ON dsa_referrals(referral_code);
        CREATE INDEX IF NOT EXISTS idx_security_log_event ON security_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_security_log_created ON security_log(created_at);
    """)
    db.commit()
    db.close()
    logger.info("CLYR database initialized at %s", _get_db_path())


def _generate_id(prefix: str = "rpt") -> str:
    return f"{prefix}_{secrets.token_hex(12)}"


# ─── Report Operations ──────────────────────────────────────────────────────

def save_report(user_id: str | None, customer_name: str, score: int, language: str,
                letter_text: str, issues: list, action_steps: list = None,
                timeline: list = None, general_health: str = "") -> str:
    """Save a generated report. Returns report ID."""
    db = get_db()
    try:
        report_id = _generate_id("rpt")
        now = time.time()

        # Build action_steps from issues if not provided
        if action_steps is None:
            action_steps = []
            for issue in issues:
                if isinstance(issue, dict) and issue.get("action"):
                    action_steps.append(issue["action"])

        # Build timeline from issues if not provided
        if timeline is None:
            timeline = []
            for i, issue in enumerate(issues):
                timeline.append({
                    "phase": f"Issue {i+1}",
                    "task": f"Resolve {issue.get('account', 'account')} — {issue.get('details', '')[:80]}",
                    "status": "Pending"
                })

        db.execute(
            """INSERT INTO reports
               (id, user_id, customer_name, score, language, letter_text,
                issues_json, action_steps_json, timeline_json, general_health,
                status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)""",
            (
                report_id,
                user_id,
                customer_name,
                score,
                language,
                letter_text,
                json.dumps(issues, ensure_ascii=False),
                json.dumps(action_steps, ensure_ascii=False),
                json.dumps(timeline, ensure_ascii=False),
                general_health,
                now,
                now,
            )
        )
        db.commit()
        logger.info("Report saved: %s for user %s", report_id, user_id)
        return report_id
    finally:
        db.close()


def get_user_reports(user_id: str) -> list:
    """Get all reports for a user, newest first."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [_row_to_report(row) for row in rows]
    finally:
        db.close()


def get_report_by_id(report_id: str) -> Optional[dict]:
    """Get a single report by ID."""
    db = get_db()
    try:
        row = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if row:
            return _row_to_report(row)
        return None
    finally:
        db.close()


def _row_to_report(row) -> dict:
    """Convert a report row to the API response format."""
    issues = json.loads(row["issues_json"] or "[]")
    action_steps = json.loads(row["action_steps_json"] or "[]")
    timeline = json.loads(row["timeline_json"] or "[]")

    # Build action_steps from issues if empty
    if not action_steps and issues:
        for issue in issues:
            if isinstance(issue, dict) and issue.get("action"):
                action_steps.append(issue["action"])

    # Build timeline from issues if empty
    if not timeline and issues:
        for i, issue in enumerate(issues):
            timeline.append({
                "phase": f"Issue {i+1}",
                "task": f"Resolve {issue.get('account', 'account')}",
                "status": "Pending"
            })

    return {
        "id": row["id"],
        "customer_name": row["customer_name"],
        "score": row["score"],
        "language": row["language"],
        "letter": row["letter_text"],
        "issues": issues,
        "action_steps": action_steps,
        "timeline": timeline,
        "general_health": row["general_health"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


# ─── Order Operations ───────────────────────────────────────────────────────

def create_order_record(user_id: str, report_id: str, plan: str, amount: int,
                        currency: str = "INR", razorpay_order_id: str = "") -> str:
    """Create an order record. Returns order ID."""
    db = get_db()
    try:
        order_id = _generate_id("ord")
        now = time.time()
        db.execute(
            """INSERT INTO orders
               (id, user_id, report_id, plan, amount, currency, razorpay_order_id,
                status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'created', ?, ?)""",
            (order_id, user_id, report_id, plan, amount, currency, razorpay_order_id, now, now)
        )
        db.commit()
        return order_id
    finally:
        db.close()


def update_order_payment(order_id: str, razorpay_payment_id: str,
                         razorpay_signature: str, status: str = "paid") -> bool:
    """Update order with payment details."""
    db = get_db()
    try:
        now = time.time()
        db.execute(
            """UPDATE orders SET razorpay_payment_id=?, razorpay_signature=?,
               status=?, updated_at=? WHERE id=?""",
            (razorpay_payment_id, razorpay_signature, status, now, order_id)
        )
        db.commit()
        return db.total_changes > 0
    finally:
        db.close()


def get_user_orders(user_id: str) -> list:
    """Get all orders for a user."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


# ─── Waitlist Operations ────────────────────────────────────────────────────

def add_to_waitlist(email: str, source: str = "landing_page") -> bool:
    """Add email to waitlist. Returns True if new, False if already exists."""
    db = get_db()
    try:
        now = time.time()
        try:
            db.execute(
                "INSERT INTO waitlist (email, source, created_at) VALUES (?, ?, ?)",
                (email.lower(), source, now)
            )
            db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        db.close()


def get_waitlist_count() -> int:
    """Get total waitlist count."""
    db = get_db()
    try:
        row = db.execute("SELECT COUNT(*) as cnt FROM waitlist").fetchone()
        return row["cnt"] if row else 0
    finally:
        db.close()


# ─── DSA Lead Operations ────────────────────────────────────────────────────

def save_dsa_leads(dsa_user_id: str, leads: list) -> int:
    """Bulk save DSA leads. Returns count saved."""
    db = get_db()
    try:
        now = time.time()
        count = 0
        for lead in leads:
            lead_id = _generate_id("lead")
            db.execute(
                """INSERT INTO dsa_leads
                   (id, dsa_user_id, client_name, score, plan, status, commission, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    lead_id,
                    dsa_user_id,
                    lead.get("name", ""),
                    lead.get("score", 0),
                    lead.get("plan", "Starter"),
                    lead.get("status", "Actioned"),
                    lead.get("commission", 100),
                    now,
                )
            )
            count += 1
        db.commit()
        return count
    finally:
        db.close()


def get_dsa_leads(dsa_user_id: str) -> list:
    """Get all leads for a DSA partner."""
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM dsa_leads WHERE dsa_user_id = ? ORDER BY created_at DESC",
            (dsa_user_id,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def get_dsa_stats(dsa_user_id: str) -> dict:
    """Get aggregated stats for a DSA partner."""
    db = get_db()
    try:
        row = db.execute(
            """SELECT COUNT(*) as total_leads,
                      SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as conversions,
                      SUM(commission) as total_commission
               FROM dsa_leads WHERE dsa_user_id = ?""",
            (dsa_user_id,)
        ).fetchone()
        return {
            "total_leads": row["total_leads"] or 0,
            "conversions": row["conversions"] or 0,
            "total_commission": row["total_commission"] or 0,
        }
    finally:
        db.close()


def get_or_create_referral(user_id: str) -> dict:
    """Get or create a referral code for a DSA partner."""
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM dsa_referrals WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)

        code = f"dsa_{secrets.token_hex(4)}"
        link = f"https://clyr.in/ref/{code}"
        now = time.time()
        db.execute(
            "INSERT INTO dsa_referrals (user_id, referral_code, referral_link, created_at) VALUES (?, ?, ?, ?)",
            (user_id, code, link, now)
        )
        db.commit()
        return {"referral_code": code, "referral_link": link}
    finally:
        db.close()


# ─── Security Log Operations ────────────────────────────────────────────────

def log_security_event(event_type: str, user_id: str = None,
                       ip_address: str = "", details: str = ""):
    """Log a security event."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO security_log (event_type, user_id, ip_address, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (event_type, user_id, ip_address, details, time.time())
        )
        db.commit()
    except Exception:
        pass  # Never fail on logging
    finally:
        db.close()


# Note: init_db() is NOT called on import to allow test fixtures to set DB path.
# Call init_db() explicitly from your application startup or test fixture.
