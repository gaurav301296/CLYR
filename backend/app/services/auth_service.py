"""
CLYR Local Auth Service
SQLite-based user store with bcrypt password hashing + PyJWT tokens.
Works without Supabase for local development and MVP.
"""
import os
import sqlite3
import secrets
import time
import logging
from pathlib import Path
from typing import Optional

import bcrypt
import jwt as pyjwt
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

def _ensure_jwt_secret():
    """Ensure JWT_SECRET exists: check env, then .env file, then generate and persist."""
    secret = os.environ.get("JWT_SECRET", "")
    if secret:
        return secret

    # Check .env file in backend directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("JWT_SECRET=") and len(line) > 11:
                secret = line[11:].strip().strip('"').strip("'")
                if secret:
                    os.environ["JWT_SECRET"] = secret
                    return secret

    # Generate a new secret and persist it
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("JWT_SECRET must be set in production")

    secret = secrets.token_hex(32)
    os.environ["JWT_SECRET"] = secret
    # Append to .env file
    with open(env_path, "a") as f:
        f.write(f"\nJWT_SECRET={secret}\n")
    logger.info("Generated new JWT_SECRET and saved to .env")
    return secret

JWT_SECRET = _ensure_jwt_secret()

JWT_EXPIRY_HOURS = 24 * 7  # 7 days
REFRESH_EXPIRY_HOURS = 24 * 30  # 30 days

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    """Get SQLite connection from shared database module."""
    from app.database import get_db as _get_db
    return _get_db()

def init_db():
    """Initialize the auth database."""
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

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
    """)
    db.commit()
    logger.info("Auth database initialized")

# ── Password Hashing (bcrypt) ─────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Hash password with bcrypt (adaptive cost, salt built-in)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False

# ── Token Helpers ─────────────────────────────────────────────────────────────

def _generate_id() -> str:
    return f"usr_{secrets.token_hex(12)}"

def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def create_access_token(user_id: str, email: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
        "type": "access",
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT access token. Returns None if invalid/expired."""
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None

# ── Password Validation ───────────────────────────────────────────────────────

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

# ── Auth Operations ───────────────────────────────────────────────────────────

def signup_user(email: str, password: str, full_name: str = "") -> dict:
    """Create a new user. Returns user dict."""
    # Validate password strength
    valid, msg = validate_password_strength(password)
    if not valid:
        raise ValueError(msg)

    db = get_db()
    try:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if existing:
            raise ValueError("User already exists")

        user_id = _generate_id()
        password_hash = _hash_password(password)
        now = time.time()

        db.execute(
            "INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email.lower(), password_hash, full_name, now, now)
        )
        db.commit()

        return {"id": user_id, "email": email.lower(), "full_name": full_name}
    finally:
        db.close()

def login_user(email: str, password: str) -> dict:
    """Authenticate user. Returns tokens and user dict."""
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if not row:
            raise ValueError("Invalid credentials")

        if not _verify_password(password, row["password_hash"]):
            raise ValueError("Invalid credentials")

        user_id = row["id"]
        access_token = create_access_token(user_id, row["email"])
        refresh_token = _generate_refresh_token()

        # Store refresh token
        db.execute(
            "INSERT INTO refresh_tokens (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (refresh_token, user_id, time.time() + (REFRESH_EXPIRY_HOURS * 3600), time.time())
        )
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user_id, "email": row["email"], "full_name": row["full_name"]},
        }
    finally:
        db.close()

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    db = get_db()
    try:
        row = db.execute("SELECT id, email, full_name, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        db.close()

def cleanup_expired_tokens():
    """Remove expired refresh tokens."""
    db = get_db()
    try:
        db.execute("DELETE FROM refresh_tokens WHERE expires_at < ?", (time.time(),))
        db.commit()
    finally:
        db.close()

# Note: db_service.init_db() is called first (on import) and creates all tables
# including users and refresh_tokens. This init_db is kept for backward compat
# but is effectively a no-op since tables already exist.
init_db()
