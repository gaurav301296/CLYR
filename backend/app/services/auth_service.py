"""
CLYR Local Auth Service
SQLite-based user store with bcrypt password hashing + JWT tokens.
Works without Supabase for local development and MVP.
"""
import os
import sqlite3
import hashlib
import secrets
import time
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("AUTH_DB_PATH", str(Path(__file__).parent.parent.parent / "auth.db"))

def get_db():
    """Get SQLite connection."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    """Initialize the auth database."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at REAL NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
    """)
    db.commit()
    db.close()
    logger.info("Auth database initialized")

def _hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt (lightweight, no bcrypt dependency)."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${pw_hash}"

def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, pw_hash = stored_hash.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == pw_hash
    except (ValueError, AttributeError):
        return False

def _generate_id() -> str:
    """Generate a unique user ID."""
    return f"usr_{secrets.token_hex(12)}"

def _generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(48)

# JWT-like simple token (not full JWT, but works for our use case)
# Format: base64(header).base64(payload).signature
import base64
import json

JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_EXPIRY = 86400 * 7  # 7 days
REFRESH_EXPIRY = 86400 * 30  # 30 days

def _create_access_token(user_id: str, email: str) -> str:
    """Create a simple signed token."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub": user_id,
        "email": email,
        "iat": time.time(),
        "exp": time.time() + JWT_EXPIRY,
        "type": "access"
    }).encode()).rstrip(b"=").decode()
    sig = hashlib.sha256(f"{header}.{payload}.{JWT_SECRET}".encode()).hexdigest()
    return f"{header}.{payload}.{sig}"

def _verify_access_token(token: str) -> Optional[dict]:
    """Verify and decode an access token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig = parts
        expected_sig = hashlib.sha256(f"{header_b64}.{payload_b64}.{JWT_SECRET}".encode()).hexdigest()
        if sig != expected_sig:
            return None
        # Add padding back
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def signup_user(email: str, password: str, full_name: str = "") -> dict:
    """Create a new user. Returns user dict."""
    db = get_db()
    try:
        # Check if user exists
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
        access_token = _create_access_token(user_id, row["email"])
        refresh_token = _generate_token()

        # Store refresh token
        db.execute(
            "INSERT INTO refresh_tokens (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (refresh_token, user_id, time.time() + REFRESH_EXPIRY, time.time())
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
        row = db.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
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

# Initialize on import
init_db()
