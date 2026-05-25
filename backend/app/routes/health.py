"""
CLYR v2 — Health Check Routes (SQLite)
GET /api/health          → Simple liveness probe
GET /api/health/detailed → Detailed status (DB, uptime)
"""
import time
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["health"])

_START_TIME = time.time()
VERSION = "2.0.0"


@router.get("/health")
async def health():
    """Simple health check."""
    return {"status": "healthy", "version": VERSION}


@router.get("/health/detailed")
async def health_detailed(user: dict = Depends(get_current_user)):
    """Detailed health check. Requires authentication. Checks DB connectivity."""
    try:
        db = get_db()
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": VERSION,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "database": db_status,
        "user": {"id": user["id"], "email": user["email"]},
    }
