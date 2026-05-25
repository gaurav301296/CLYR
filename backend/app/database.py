"""
CLYR v2 — Database Module (Hybrid)
Provides both SQLite (local) and Supabase clients.
Routes use SQLite by default; Supabase available for gradual migration.
"""
import os
import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── SQLite (local) ────────────────────────────────────────────────────────────

_DB_PATH = None

def _get_db_path():
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.environ.get("CLYR_DB_PATH", str(Path(__file__).parent.parent / "clyr.db"))
    return _DB_PATH


def get_db():
    """Get SQLite connection with WAL mode."""
    db = sqlite3.connect(_get_db_path(), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=5000")
    return db


def init_db():
    """Initialize all database tables."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at REAL NOT NULL,
            created_at REAL NOT NULL
        );

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

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            report_id TEXT,
            plan TEXT DEFAULT 'Starter',
            amount INTEGER DEFAULT 0,
            currency TEXT DEFAULT 'INR',
            razorpay_order_id TEXT DEFAULT '',
            razorpay_payment_id TEXT DEFAULT '',
            razorpay_signature TEXT DEFAULT '',
            status TEXT DEFAULT 'created',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'landing_page',
            converted INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

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

        CREATE TABLE IF NOT EXISTS dsa_referrals (
            user_id TEXT PRIMARY KEY,
            referral_code TEXT UNIQUE NOT NULL,
            referral_link TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            user_id TEXT,
            details TEXT DEFAULT '',
            created_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_razorpay ON orders(razorpay_order_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)
    db.commit()
    logger.info("SQLite database initialized at %s", _get_db_path())


# ── Supabase (optional, for future use) ──────────────────────────────────────

_supabase = None
_supabase_admin = None

def get_supabase():
    """Get Supabase client (anon key, respects RLS). Returns None if not configured."""
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client, Client
            from app.config import config
            if config.supabase_url and config.supabase_anon_key:
                _supabase = create_client(config.supabase_url, config.supabase_anon_key)
        except Exception as e:
            logger.warning("Supabase client init failed: %s", e)
    return _supabase


def get_supabase_admin():
    """Get Supabase admin client. Returns None if not configured."""
    global _supabase_admin
    if _supabase_admin is None:
        try:
            from supabase import create_client, Client
            from app.config import config
            if config.supabase_url and config.supabase_service_role_key:
                _supabase_admin = create_client(config.supabase_url, config.supabase_service_role_key)
        except Exception as e:
            logger.warning("Supabase admin client init failed: %s", e)
    return _supabase_admin


# ── DB helper functions (SQLite replacements for Supabase calls) ──────────────

def db_insert(table: str, data: dict) -> dict:
    """Insert a row into a SQLite table. Returns the inserted row as dict."""
    db = get_db()
    now = time.time()
    if "created_at" not in data:
        data["created_at"] = now
    if "updated_at" not in data:
        data["updated_at"] = now

    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = [json.dumps(v) if isinstance(v, (list, dict)) else v for v in data.values()]

    cur = db.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
    db.commit()

    # Fetch back by lastrowid or by id
    row_id = data.get("id") or cur.lastrowid
    row = db.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row:
        return dict(row)
    return data


def db_select(table: str, filters: dict = None, order_by: str = None, limit: int = None) -> list:
    """Select rows from SQLite table. Returns list of dicts."""
    db = get_db()
    query = f"SELECT * FROM {table}"
    values = []

    if filters:
        clauses = []
        for k, v in filters.items():
            clauses.append(f"{k} = ?")
            values.append(v)
        query += " WHERE " + " AND ".join(clauses)

    if order_by:
        direction = "ASC"
        if order_by.startswith("-"):
            direction = "DESC"
            order_by = order_by[1:]
        query += f" ORDER BY {order_by} {direction}"

    if limit:
        query += f" LIMIT {limit}"

    rows = db.execute(query, values).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        # Auto-parse JSON fields
        for key, val in d.items():
            if isinstance(val, str) and key.endswith(("_json",)):
                try:
                    d[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        result.append(d)
    return result


def db_update(table: str, data: dict, filters: dict) -> dict:
    """Update rows in SQLite table. Returns the updated row."""
    db = get_db()
    data["updated_at"] = time.time()

    set_clauses = []
    values = []
    for k, v in data.items():
        if k == "id":
            continue
        set_clauses.append(f"{k} = ?")
        values.append(json.dumps(v) if isinstance(v, (list, dict)) else v)

    where_clauses = []
    for k, v in filters.items():
        where_clauses.append(f"{k} = ?")
        values.append(v)

    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    db.execute(query, values)
    db.commit()

    return data


def db_count(table: str, filters: dict = None) -> int:
    """Count rows in SQLite table."""
    db = get_db()
    query = f"SELECT COUNT(*) FROM {table}"
    values = []
    if filters:
        clauses = []
        for k, v in filters.items():
            clauses.append(f"{k} = ?")
            values.append(v)
        query += " WHERE " + " AND ".join(clauses)
    row = db.execute(query, values).fetchone()
    return row[0] if row else 0
