import os
import razorpay
from typing import Optional

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

PLAN_PRICES = {
    "Starter": 49900,    # 499 INR in paise
    "Follow-up": 79900,  # 799 INR in paise
    "Recovery": 129900,  # 1299 INR in paise
}

_client = None


def get_razorpay_client():
    global _client
    if _client is None:
        _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    return _client


def create_order(plan: str, user_id: str, report_id: str) -> dict:
    """Create a Razorpay order. Returns order details."""
    if plan not in PLAN_PRICES:
        raise ValueError(f"Invalid plan: {plan}")

    amount = PLAN_PRICES[plan]
    client = get_razorpay_client()

    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"clyr_{report_id[:8]}",
        "notes": {
            "plan": plan,
            "user_id": user_id,
            "report_id": report_id,
        }
    }

    order = client.order.create(data=order_data)
    return {
        "razorpay_order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "plan": plan,
    }


def verify_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify Razorpay payment signature."""
    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def get_payment_details(payment_id: str) -> Optional[dict]:
    """Fetch payment details from Razorpay."""
    client = get_razorpay_client()
    try:
        payment = client.payment.fetch(payment_id)
        return {
            "id": payment["id"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "status": payment["status"],
            "method": payment.get("method", ""),
            "email": payment.get("email", ""),
            "contact": payment.get("contact", ""),
        }
    except Exception:
        return None
