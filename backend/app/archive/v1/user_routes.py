import os
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.middleware.auth import get_current_user, get_optional_user
from app.services.auth_service import signup_user, login_user, get_user_by_id
from app.services.payment_service import create_order, verify_payment, PLAN_PRICES
from app.services import db_service

router = APIRouter(prefix="/api", tags=["user"])


class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "landing_page"


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
        db_service.log_security_event("signup", user_id=user["id"])
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
        db_service.log_security_event("login", user_id=result["user"]["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Logout current user (client-side token removal)."""
    db_service.log_security_event("logout", user_id=user["id"])
    return {"message": "Logged out successfully"}


@router.get("/user/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


# ─── Reports Routes ──────────────────────────────────────────────────────────

@router.get("/user/reports")
async def get_my_reports(user: dict = Depends(get_current_user)):
    """Get all reports for current user."""
    reports = db_service.get_user_reports(user["id"])
    return reports


@router.get("/user/reports/{report_id}")
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Get a specific report by ID."""
    report = db_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ─── Waitlist Route ──────────────────────────────────────────────────────────

@router.post("/waitlist")
async def join_waitlist(req: WaitlistRequest):
    """Add email to waitlist."""
    added = db_service.add_to_waitlist(req.email, req.source)
    count = db_service.get_waitlist_count()
    if added:
        return {"message": "Added to waitlist", "email": req.email, "position": count}
    return {"message": "Already on waitlist", "email": req.email, "position": count}


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
        # Save order to DB
        db_service.create_order_record(
            user_id=user["id"],
            report_id=report_id,
            plan=plan,
            amount=order["amount"],
            currency=order["currency"],
            razorpay_order_id=order["razorpay_order_id"],
        )
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
        db_service.log_security_event("payment_failed", user_id=user["id"],
                                     details=f"Order: {req.razorpay_order_id}")
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Update order in DB
    db_service.update_order_payment(
        order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
        status="paid",
    )
    db_service.log_security_event("payment_success", user_id=user["id"],
                                 details=f"Order: {req.razorpay_order_id}")
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
    """Get DSA partner stats for the authenticated user."""
    return db_service.get_dsa_stats(user["id"])


@router.get("/dsa/leads")
async def get_dsa_leads(user: dict = Depends(get_current_user)):
    """Get all leads for the authenticated DSA partner."""
    leads = db_service.get_dsa_leads(user["id"])
    # Format for frontend
    return [{
        "name": lead["client_name"],
        "score": lead["score"],
        "date": lead["created_at"],
        "plan": lead["plan"],
        "status": lead["status"],
        "commission": lead["commission"],
    } for lead in leads]


@router.post("/dsa/leads")
async def create_dsa_leads(
    leads: list[DsaLeadRequest],
    user: dict = Depends(get_current_user),
):
    """Bulk create leads for the authenticated DSA partner."""
    lead_dicts = [lead.model_dump() for lead in leads]
    count = db_service.save_dsa_leads(user["id"], lead_dicts)
    return {"message": f"Created {count} leads", "count": count}


@router.get("/dsa/referral-link")
async def get_referral_link(user: dict = Depends(get_current_user)):
    """Get or create referral link for the authenticated DSA partner."""
    ref = db_service.get_or_create_referral(user["id"])
    return {
        "referral_code": ref["referral_code"],
        "referral_link": ref["referral_link"],
    }
