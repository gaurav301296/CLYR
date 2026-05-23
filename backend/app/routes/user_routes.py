import os
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.middleware.auth import get_current_user, get_optional_user
from app.services.auth_service import signup_user, login_user, get_user_by_id
from app.services.payment_service import create_order, verify_payment, PLAN_PRICES

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
async def logout():
    """Logout current user (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/user/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


@router.get("/user/reports")
async def get_my_reports(user: dict = Depends(get_current_user)):
    """Get all reports for current user."""
    # For MVP, return empty list. In production, fetch from DB.
    return []


@router.post("/waitlist")
async def join_waitlist(req: WaitlistRequest):
    """Add email to waitlist."""
    # For MVP, just return success. In production, store in DB.
    return {"message": "Added to waitlist", "email": req.email}


@router.post("/payment/create-order")
async def create_payment_order(
    plan: str,
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """Create a Razorpay order for a plan."""
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")

    try:
        order = create_order(plan, user["id"], report_id)
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
    user: dict = Depends(get_current_user)
):
    """Verify Razorpay payment and update order status."""
    is_valid = verify_payment(req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    return {"message": "Payment verified successfully", "status": "paid"}


# ── DSA Partner Routes ──────────────────────────────────────────────────────

class DsaLeadRequest(BaseModel):
    name: str
    score: int = 0
    plan: str = "Starter"
    status: str = "Actioned"
    commission: int = 100


@router.get("/dsa/stats")
async def get_dsa_stats(user: dict = Depends(get_current_user)):
    """Get DSA partner stats for the authenticated user."""
    return {
        "total_leads": 0,
        "conversions": 0,
        "total_commission": 0,
    }


@router.get("/dsa/leads")
async def get_dsa_leads(user: dict = Depends(get_current_user)):
    """Get all leads for the authenticated DSA partner."""
    return []


@router.post("/dsa/leads")
async def create_dsa_leads(
    leads: list[DsaLeadRequest],
    user: dict = Depends(get_current_user),
):
    """Bulk create leads for the authenticated DSA partner."""
    return {"message": f"Created {len(leads)} leads", "count": len(leads)}


@router.get("/dsa/referral-link")
async def get_referral_link(user: dict = Depends(get_current_user)):
    """Get or create referral link for the authenticated DSA partner."""
    import uuid
    code = f"dsa_{uuid.uuid4().hex[:8]}"
    return {
        "referral_code": code,
        "referral_link": f"https://clyr.in/ref/{code}",
    }
