"""
CLYR v2 — Payment Routes (SQLite)
Razorpay integration: create-order, verify-payment, webhook.
Uses SQLite for order storage.
"""
import hashlib
import hmac
import json
import logging
import os
import time
from uuid import uuid4

import razorpay
from fastapi import APIRouter, HTTPException, Request

from app.config import config
from app.database import db_insert, db_select, db_update, get_db
from app.middleware.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

# Plan prices in paise (INR * 100)
PLAN_PRICES = {
    "Starter": 49900,      # ₹499
    "Follow-up": 79900,    # ₹799
    "Recovery": 149900,    # ₹1499
}

_razorpay_client: razorpay.Client | None = None


def get_razorpay_client() -> razorpay.Client | None:
    global _razorpay_client
    if _razorpay_client is None:
        if config.razorpay_key_id and config.razorpay_key_secret:
            _razorpay_client = razorpay.Client(
                auth=(config.razorpay_key_id, config.razorpay_key_secret)
            )
    return _razorpay_client


def _mock_order(plan: str) -> dict:
    """Create a mock order for dev/testing when Razorpay keys aren't configured."""
    order_id = f"order_{uuid4().hex[:20]}"
    return {"id": order_id, "amount": PLAN_PRICES.get(plan, 49900), "currency": "INR"}


# ── POST /api/payments/create-order ─────────────────────────────────────────

@router.post("/create-order")
async def create_order(request: Request):
    """Create a Razorpay order and store it in SQLite."""
    body = await request.json()
    plan = body.get("plan", "Starter")
    report_id = body.get("report_id")

    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")

    amount = PLAN_PRICES[plan]

    user = await get_optional_user(request)
    user_id = user["id"] if user else None

    rp = get_razorpay_client()

    if rp:
        try:
            rp_order = rp.order.create(data={
                "amount": amount,
                "currency": "INR",
                "receipt": f"clyr_{plan.lower()}_{user_id or 'anon'}",
                "notes": {"plan": plan, "report_id": report_id or "", "user_id": user_id or ""},
            })
            razorpay_order_id = rp_order["id"]
        except Exception as e:
            logger.error("Razorpay order creation failed: %s", e)
            raise HTTPException(status_code=502, detail=f"Razorpay error: {e}")
    else:
        # Mock mode for dev
        mock = _mock_order(plan)
        razorpay_order_id = mock["id"]

    # Store in SQLite
    order_id = str(uuid4())
    now = time.time()
    order_data = {
        "id": order_id,
        "user_id": user_id or "anonymous",
        "report_id": report_id,
        "plan": plan,
        "amount": amount,
        "currency": "INR",
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": "",
        "razorpay_signature": "",
        "status": "created",
        "created_at": now,
        "updated_at": now,
    }

    try:
        db_insert("orders", order_data)
    except Exception as e:
        logger.error("Failed to store order: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create local order record")

    return {
        "order_id": order_id,
        "razorpay_order_id": razorpay_order_id,
        "amount": amount,
        "currency": "INR",
        "plan": plan,
        "razorpay_key_id": config.razorpay_key_id or "rzp_test_placeholder",
    }


# ── POST /api/payments/verify ────────────────────────────────────────────────

@router.post("/verify")
async def verify_payment(request: Request):
    """Verify a Razorpay payment signature and update order status."""
    body = await request.json()
    razorpay_order_id = body.get("razorpay_order_id", "")
    razorpay_payment_id = body.get("razorpay_payment_id", "")
    razorpay_signature = body.get("razorpay_signature", "")

    rp = get_razorpay_client()

    if rp:
        try:
            rp.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError as e:
            logger.warning("Razorpay signature verification failed: %s", e)
            raise HTTPException(status_code=400, detail="Invalid payment signature")
    else:
        # Mock mode: accept all verifications
        logger.info("Mock mode: accepting payment verification for order %s", razorpay_order_id)

    # Update order in SQLite
    orders = db_select("orders", filters={"razorpay_order_id": razorpay_order_id})
    if not orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[0]
    db_update("orders", {
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
        "status": "paid",
    }, {"id": order["id"]})

    logger.info("Payment verified for order %s", order["id"])
    return {"message": "Payment verified successfully", "status": "paid"}


# ── POST /api/payments/webhook ───────────────────────────────────────────────

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay webhook endpoint. Verifies signature and updates order status."""
    body = await request.body()
    body_text = body.decode("utf-8")

    webhook_secret = config.razorpay_key_secret
    dedicated_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    if dedicated_secret:
        webhook_secret = dedicated_secret

    signature = request.headers.get("X-Razorpay-Signature", "")
    if webhook_secret:
        expected = hmac.new(
            key=webhook_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("Razorpay webhook signature mismatch")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = json.loads(body_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = event.get("event", "")
    payload = event.get("payload", {})
    rp_order = payload.get("order", {})
    rp_order_id = rp_order.get("entity", {}).get("id", "")

    logger.info("Razorpay webhook: %s (order=%s)", event_name, rp_order_id)

    if event_name == "order.paid":
        orders = db_select("orders", filters={"razorpay_order_id": rp_order_id})
        if orders:
            db_update("orders", {"status": "paid"}, {"id": orders[0]["id"]})
            logger.info("Order %s marked as paid via webhook", rp_order_id)
    elif event_name == "payment.failed":
        orders = db_select("orders", filters={"razorpay_order_id": rp_order_id})
        if orders:
            db_update("orders", {"status": "failed"}, {"id": orders[0]["id"]})

    return {"status": "ok"}
