"""
CLYR v2 — User Routes (SQLite + JWT)
Auth, reports, payments, DSA — all using local SQLite.
"""
import os
import json
import time
import logging
from uuid import uuid4
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.middleware.auth import get_current_user, get_optional_user
from app.services.auth_service import signup_user, login_user, get_user_by_id
from app.services.payment_service import create_order, verify_payment, PLAN_PRICES
from app.database import db_insert, db_select, db_update, db_count, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["user"])


class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    report_id: str


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@router.post("/auth/signup")
async def signup(req: EmailSignupRequest):
    """Sign up a new user with email + password."""
    try:
        user = signup_user(req.email, req.password, req.full_name)
        return {"message": "Signup successful.", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/auth/login")
async def login(req: EmailSignupRequest):
    """Login with email + password."""
    try:
        result = login_user(req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Logout current user (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/user/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


# ─── Reports Routes ──────────────────────────────────────────────────────────

@router.get("/user/reports")
async def get_my_reports(user: dict = Depends(get_current_user)):
    """Get all reports for current user."""
    reports = db_select("reports", filters={"user_id": user["id"]}, order_by="-created_at")
    return reports


@router.get("/user/reports/{report_id}")
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Get a specific report by ID."""
    rows = db_select("reports", filters={"id": report_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")
    return rows[0]


# ─── Payment Routes ──────────────────────────────────────────────────────────

@router.post("/payment/create-order")
async def create_payment_order(
    plan: str,
    report_id: str,
    user: dict = Depends(get_current_user),
):
    """Create a Razorpay order for a plan."""
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")

    try:
        order = create_order(plan, user["id"], report_id)
        db_insert("orders", {
            "id": str(uuid4()),
            "user_id": user["id"],
            "report_id": report_id,
            "plan": plan,
            "amount": order["amount"],
            "currency": order["currency"],
            "razorpay_order_id": order["razorpay_order_id"],
            "status": "created",
            "created_at": time.time(),
            "updated_at": time.time(),
        })
        return {
            "order_id": order["razorpay_order_id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "plan": plan,
            "razorpay_key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
            "report_id": report_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/payment/verify")
async def verify_payment_endpoint(
    req: RazorpayVerifyRequest,
    user: dict = Depends(get_current_user),
):
    """Verify Razorpay payment and update order status."""
    is_valid = verify_payment(req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    orders = db_select("orders", filters={"razorpay_order_id": req.razorpay_order_id})
    if orders:
        db_update("orders", {
            "razorpay_payment_id": req.razorpay_payment_id,
            "razorpay_signature": req.razorpay_signature,
            "status": "paid",
        }, {"id": orders[0]["id"]})

    return {"message": "Payment verified successfully", "status": "paid"}


# ─── DSA Partner Routes ──────────────────────────────────────────────────────

class DsaLeadRequest(BaseModel):
    name: str
    score: int = 0
    plan: str = "Starter"
    status: str = "Actioned"
    commission: int = 100


@router.get("/dsa/stats")
async def get_dsa_stats(user: dict = Depends(get_current_user)):
    """Get DSA partner stats."""
    db = get_db()
    leads = db.execute(
        "SELECT COUNT(*) as total, SUM(commission) as total_commission FROM dsa_leads WHERE dsa_user_id = ?",
        (user["id"],),
    ).fetchone()
    return {
        "total_leads": leads["total"] if leads else 0,
        "total_commission": leads["total_commission"] if leads else 0,
    }


@router.get("/dsa/leads")
async def get_dsa_leads(user: dict = Depends(get_current_user)):
    """Get all leads for the authenticated DSA partner."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM dsa_leads WHERE dsa_user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    return [{
        "name": l["client_name"],
        "score": l["score"],
        "date": l["created_at"],
        "plan": l["plan"],
        "status": l["status"],
        "commission": l["commission"],
    } for l in (dict(r) for r in rows)]


@router.post("/dsa/leads")
async def create_dsa_leads(
    leads: list[DsaLeadRequest],
    user: dict = Depends(get_current_user),
):
    """Bulk create leads for the authenticated DSA partner."""
    db = get_db()
    count = 0
    for lead in leads:
        lead_id = f"dsa_{uuid4().hex[:12]}"
        db.execute(
            "INSERT INTO dsa_leads (id, dsa_user_id, client_name, score, plan, status, commission, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (lead_id, user["id"], lead.name, lead.score, lead.plan, lead.status, lead.commission, time.time()),
        )
        count += 1
    db.commit()
    return {"message": f"Created {count} leads", "count": count}


@router.get("/dsa/referral-link")
async def get_referral_link(user: dict = Depends(get_current_user)):
    """Get or create referral link for the authenticated DSA partner."""
    db = get_db()
    row = db.execute("SELECT * FROM dsa_referrals WHERE user_id = ?", (user["id"],)).fetchone()
    if not row:
        code = f"CLYR-{uuid4().hex[:8].upper()}"
        link = f"https://clyr.in/ref/{code}"
        db.execute(
            "INSERT INTO dsa_referrals (user_id, referral_code, referral_link, created_at) VALUES (?, ?, ?, ?)",
            (user["id"], code, link, time.time()),
        )
        db.commit()
        return {"referral_code": code, "referral_link": link}
    d = dict(row)
    return {"referral_code": d["referral_code"], "referral_link": d["referral_link"]}
