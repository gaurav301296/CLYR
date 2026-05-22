import os
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.middleware.auth import get_current_user, get_optional_user
from app.services.supabase_client import get_supabase, get_supabase_admin
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
        sb = get_supabase()
        result = sb.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {"data": {"full_name": req.full_name}},
        })
        return {"message": "Signup successful. Check your email for verification.", "user": result.user.id if result.user else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
async def login(req: EmailSignupRequest):
    """Login with email + password."""
    try:
        sb = get_supabase()
        result = sb.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": {"id": result.user.id, "email": result.user.email},
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/auth/logout")
async def logout():
    """Logout current user."""
    try:
        sb = get_supabase()
        sb.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    try:
        admin = get_supabase_admin()
        profile = admin.table("profiles").select("*").eq("id", user["id"]).single().execute()
        return profile.data
    except Exception as e:
        return {"id": user["id"], "email": user["email"]}


@router.get("/user/reports")
async def get_my_reports(user: dict = Depends(get_current_user)):
    """Get all reports for current user."""
    try:
        admin = get_supabase_admin()
        reports = admin.table("reports").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        return reports.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/reports")
async def save_report(user: dict = Depends(get_current_user)):
    """Save a report for current user."""
    # This is handled via the existing /api/upload endpoint
    pass


@router.post("/waitlist")
async def join_waitlist(req: WaitlistRequest):
    """Add email to waitlist."""
    try:
        admin = get_supabase_admin()
        result = admin.table("waitlist").insert({
            "email": req.email,
            "source": req.source,
        }).execute()
        return {"message": "Added to waitlist", "email": req.email}
    except Exception as e:
        # Duplicate email is OK
        if "duplicate" in str(e).lower() or "23505" in str(e):
            return {"message": "Already on waitlist", "email": req.email}
        raise HTTPException(status_code=400, detail=str(e))


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

        # Save order to database
        admin = get_supabase_admin()
        admin.table("orders").insert({
            "user_id": user["id"],
            "report_id": report_id,
            "razorpay_order_id": order["razorpay_order_id"],
            "plan": plan,
            "amount": order["amount"],
            "status": "created",
        }).execute()

        return {
            "order_id": order["razorpay_order_id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "plan": plan,
            "razorpay_key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
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

    try:
        admin = get_supabase_admin()
        admin.table("orders").update({
            "razorpay_payment_id": req.razorpay_payment_id,
            "razorpay_signature": req.razorpay_signature,
            "status": "paid",
        }).eq("razorpay_order_id", req.razorpay_order_id).execute()

        return {"message": "Payment verified successfully", "status": "paid"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")


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
    try:
        admin = get_supabase_admin()
        partner = admin.table("dsa_partners").select("*").eq("user_id", user["id"]).single().execute()
        leads = admin.table("reports").select("id, status, created_at").eq("user_id", user["id"]).execute()
        total_leads = len(leads.data) if leads.data else 0
        conversions = len([l for l in (leads.data or []) if l.get("status") == "completed"])
        total_commission = (partner.data or {}).get("total_earnings", 0)
        return {
            "total_leads": total_leads,
            "conversions": conversions,
            "total_commission": total_commission,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch DSA stats: {str(e)}")


@router.get("/dsa/leads")
async def get_dsa_leads(user: dict = Depends(get_current_user)):
    """Get all leads for the authenticated DSA partner."""
    try:
        admin = get_supabase_admin()
        leads = admin.table("reports").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        return leads.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")


@router.post("/dsa/leads")
async def create_dsa_leads(
    leads: list[DsaLeadRequest],
    user: dict = Depends(get_current_user),
):
    """Bulk create leads for the authenticated DSA partner."""
    try:
        admin = get_supabase_admin()
        rows = [{"user_id": user["id"], **l.model_dump()} for l in leads]
        result = admin.table("reports").insert(rows).execute()
        return {"message": f"Created {len(result.data or [])} leads", "count": len(result.data or [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create leads: {str(e)}")


@router.get("/dsa/referral-link")
async def get_referral_link(user: dict = Depends(get_current_user)):
    """Get or create referral link for the authenticated DSA partner."""
    try:
        admin = get_supabase_admin()
        partner = admin.table("dsa_partners").select("*").eq("user_id", user["id"]).single().execute()
        if partner.data:
            code = partner.data["referral_code"]
        else:
            import uuid
            code = f"dsa_{uuid.uuid4().hex[:8]}"
            admin.table("dsa_partners").insert({
                "user_id": user["id"],
                "referral_code": code,
            }).execute()
        return {
            "referral_code": code,
            "referral_link": f"https://clyr.in/ref/{code}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get referral link: {str(e)}")
