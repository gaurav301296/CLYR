"""
CLYR v2 — Pydantic Models for all API requests/responses
Strict validation on all inputs. No garbage in.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum


class PlanType(str, Enum):
    STARTER = "Starter"
    FOLLOWUP = "Follow-up"
    RECOVERY = "Recovery"

    @classmethod
    def prices(cls) -> dict:
        return {
            cls.STARTER: 49900,
            cls.FOLLOWUP: 79900,
            cls.RECOVERY: 129900,
        }

    @classmethod
    def price_inr(cls, plan: str) -> int:
        p = cls.prices().get(plan, 49900)
        return p // 100


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str = ""
    role: str = "user"


class Issue(BaseModel):
    account: str
    type: str
    details: str
    impact: str
    action: str = ""


class ActionStep(BaseModel):
    step: str
    completed: bool = False


class TimelineItem(BaseModel):
    phase: str
    task: str
    status: str


class ReportResponse(BaseModel):
    id: str
    customer_name: str = ""
    score: int = Field(ge=300, le=900)
    language: str = "en"
    letter: str = ""
    issues: list[Issue] = []
    action_steps: list[str] = []
    timeline: list[TimelineItem] = []
    general_health: str = ""
    status: str = "processing"
    pdf_url: str = ""
    created_at: str = ""


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int


class CreateOrderRequest(BaseModel):
    plan: PlanType
    report_id: str | None = None


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str = "INR"
    plan: str
    razorpay_key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    message: str
    status: str


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "landing_page"


class WaitlistResponse(BaseModel):
    message: str
    email: str
    position: int | None = None


class DsaLeadRequest(BaseModel):
    name: str
    client_email: str = ""
    score: int = 0
    plan: str = "Starter"
    status: str = "Actioned"
    commission: int = 100


class DsaStatsResponse(BaseModel):
    total_leads: int
    conversions: int
    total_commission: int


class ReferralResponse(BaseModel):
    referral_code: str
    referral_link: str
    total_clicks: int = 0
    total_conversions: int = 0


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_reports: int
    total_orders: int
    total_revenue: int
    total_waitlist: int
    recent_signups: list[UserProfile]
    recent_orders: list[dict]
