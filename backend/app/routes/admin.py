"""
CLYR v2 — Admin Routes (SQLite)
All routes require the authenticated user to have role='admin'.
"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.database import db_select, db_count, get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that verifies the current user has admin role."""
    # Check role from users table
    rows = db_select("users", filters={"id": user["id"]})
    if not rows or rows[0].get("role") != "admin":
        logger.warning("Unauthorized admin access attempt by user %s", user["id"])
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/dashboard")
async def admin_dashboard(admin: dict = Depends(require_admin)):
    """Return dashboard statistics."""
    stats = {}
    stats["total_users"] = db_count("users")
    stats["total_reports"] = db_count("reports")
    stats["paid_orders"] = db_count("orders", filters={"status": "paid"})
    stats["waitlist_count"] = db_count("waitlist")

    # Revenue
    try:
        paid = db_select("orders", filters={"status": "paid"})
        stats["total_revenue"] = sum(o.get("amount", 0) for o in paid)
    except Exception:
        stats["total_revenue"] = 0

    return stats


@router.get("/users")
async def admin_list_users(
    page: int = 1,
    per_page: int = 50,
    admin: dict = Depends(require_admin),
):
    """Return paginated list of users."""
    try:
        db = get_db()
        offset = (page - 1) * per_page
        rows = db.execute(
            "SELECT id, email, full_name, role, created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()
        return {
            "page": page,
            "per_page": per_page,
            "users": [dict(r) for r in rows],
        }
    except Exception as e:
        logger.error("Failed to list users: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {e}")


@router.get("/waitlist")
async def admin_list_waitlist(
    page: int = 1,
    per_page: int = 50,
    admin: dict = Depends(require_admin),
):
    """Return paginated list of waitlist entries."""
    try:
        db = get_db()
        offset = (page - 1) * per_page
        rows = db.execute(
            "SELECT id, email, source, created_at FROM waitlist ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()
        return {
            "page": page,
            "per_page": per_page,
            "entries": [dict(r) for r in rows],
        }
    except Exception as e:
        logger.error("Failed to list waitlist: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch waitlist: {e}")
