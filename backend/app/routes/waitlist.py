"""
CLYR v2 — Waitlist Route (SQLite)
POST /api/waitlist — Add email to the waitlist table.
"""
import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import db_insert, db_select, db_count

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waitlist"])


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "landing_page"


class WaitlistResponse(BaseModel):
    message: str
    email: str
    position: int


@router.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(req: WaitlistRequest):
    """Add an email to the waitlist. Idempotent — duplicate emails return success."""
    # Check if already exists
    existing = db_select("waitlist", filters={"email": req.email})
    if existing:
        total = db_count("waitlist")
        return WaitlistResponse(message="Already on waitlist", email=req.email, position=total)

    try:
        db_insert("waitlist", {
            "email": req.email,
            "source": req.source,
            "converted": 0,
            "created_at": time.time(),
        })
        total = db_count("waitlist")
        return WaitlistResponse(message="Added to waitlist", email=req.email, position=total)
    except Exception as e:
        logger.error("Failed to add to waitlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add to waitlist")
