"""
Tests for CLYR auth, payment, DSA, and upload routes.
"""
import os
import io
import uuid
import tempfile
import pytest
from fastapi.testclient import TestClient

# Setup test environment BEFORE importing app
_temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["CLYR_DB_PATH"] = _temp_db.name
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-production"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_placeholder"
os.environ["RAZORPAY_KEY_SECRET"] = "placeholder"
os.environ["SENTRY_DSN"] = ""
os.environ["OPENAI_API_KEY"] = "placeholder"  # Forces regex fallback
os.environ["RATE_LIMIT_RPM"] = "10000"  # Disable rate limiting for tests
os.environ["RATE_LIMIT_UPLOAD_RPM"] = "10000"

from app.main import app

client = TestClient(app)


def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


# ─── Auth Tests ──────────────────────────────────────────────────────────────

class TestAuth:
    def test_signup_success(self):
        resp = client.post("/api/auth/signup", json={
            "email": unique_email(),
            "password": "SecurePass123!",
            "full_name": "Test User",
        })
        assert resp.status_code == 200
        assert "user" in resp.json()

    def test_signup_duplicate_email(self):
        email = unique_email()
        # First signup
        resp1 = client.post("/api/auth/signup", json={
            "email": email, "password": "SecurePass123!",
        })
        assert resp1.status_code == 200
        # Duplicate
        resp2 = client.post("/api/auth/signup", json={
            "email": email, "password": "AnotherPass123!",
        })
        assert resp2.status_code == 400
        assert "already exists" in resp2.json()["detail"].lower()

    def test_login_success(self):
        email = unique_email()
        password = "SecurePass123!"
        # Signup first
        client.post("/api/auth/signup", json={
            "email": email, "password": password, "full_name": "Login Test",
        })
        # Login
        resp = client.post("/api/auth/login", json={
            "email": email, "password": password,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == email

    def test_login_wrong_password(self):
        email = unique_email()
        client.post("/api/auth/signup", json={
            "email": email, "password": "CorrectPass123!",
        })
        resp = client.post("/api/auth/login", json={
            "email": email, "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@example.com", "password": "SomePass123!",
        })
        assert resp.status_code == 401

    def test_get_profile_authenticated(self):
        email = unique_email()
        # Signup + login
        client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        login_resp = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
        token = login_resp.json()["access_token"]

        resp = client.get("/api/user/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["email"] == email

    def test_get_profile_unauthenticated(self):
        resp = client.get("/api/user/me")
        assert resp.status_code == 401

    def test_logout(self):
        email = unique_email()
        client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        login_resp = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
        token = login_resp.json()["access_token"]

        resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_token_invalid(self):
        resp = client.get("/api/user/me", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    def test_token_missing(self):
        resp = client.get("/api/user/me", headers={})
        assert resp.status_code == 401


# ─── Reports Tests ───────────────────────────────────────────────────────────

class TestReports:
    def _get_token(self):
        email = unique_email()
        client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        resp = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
        return resp.json()["access_token"]

    def test_get_reports_authenticated(self):
        token = self._get_token()
        resp = client.get("/api/user/reports", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_reports_unauthenticated(self):
        resp = client.get("/api/user/reports")
        assert resp.status_code == 401


# ─── Waitlist Tests ──────────────────────────────────────────────────────────

class TestWaitlist:
    def test_join_waitlist(self):
        resp = client.post("/api/waitlist", json={
            "email": unique_email(),
            "source": "landing_page",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "position" in data

    def test_join_waitlist_duplicate(self):
        email = unique_email()
        client.post("/api/waitlist", json={"email": email})
        resp = client.post("/api/waitlist", json={"email": email})
        assert resp.status_code == 200
        assert "already" in resp.json()["message"].lower()

    def test_join_waitlist_invalid_email(self):
        resp = client.post("/api/waitlist", json={"email": "not-an-email"})
        assert resp.status_code == 422


# ─── Payment Tests ───────────────────────────────────────────────────────────

class TestPayment:
    def _get_token(self):
        email = unique_email()
        client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        resp = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
        return resp.json()["access_token"]

    def test_create_order_success(self):
        token = self._get_token()
        resp = client.post(
            "/api/payment/create-order?plan=Starter&report_id=rpt_test123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "order_id" in data
        assert data["amount"] == 49900
        assert data["currency"] == "INR"

    def test_create_order_followup(self):
        token = self._get_token()
        resp = client.post(
            "/api/payment/create-order?plan=Follow-up&report_id=rpt_test456",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 79900

    def test_create_order_recovery(self):
        token = self._get_token()
        resp = client.post(
            "/api/payment/create-order?plan=Recovery&report_id=rpt_test789",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 129900

    def test_create_order_invalid_plan(self):
        token = self._get_token()
        resp = client.post(
            "/api/payment/create-order?plan=InvalidPlan&report_id=rpt_test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_create_order_unauthenticated(self):
        resp = client.post(
            "/api/payment/create-order?plan=Starter&report_id=rpt_test",
        )
        assert resp.status_code == 401

    def test_verify_payment_mock(self):
        token = self._get_token()
        create_resp = client.post(
            "/api/payment/create-order?plan=Starter&report_id=rpt_verify_test",
            headers={"Authorization": f"Bearer {token}"},
        )
        order_id = create_resp.json()["order_id"]

        resp = client.post("/api/payment/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": "pay_mock123",
                "razorpay_signature": "mock_sig",
                "report_id": "rpt_verify_test",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "paid"


# ─── DSA Tests ───────────────────────────────────────────────────────────────

class TestDSA:
    def _get_token(self):
        email = unique_email()
        client.post("/api/auth/signup", json={"email": email, "password": "Pass123!"})
        resp = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
        return resp.json()["access_token"]

    def test_get_dsa_stats(self):
        token = self._get_token()
        resp = client.get("/api/dsa/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_leads" in data
        assert "conversions" in data
        assert "total_commission" in data

    def test_get_dsa_leads_empty(self):
        token = self._get_token()
        resp = client.get("/api/dsa/leads", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_dsa_leads(self):
        token = self._get_token()
        resp = client.post("/api/dsa/leads",
            headers={"Authorization": f"Bearer {token}"},
            json=[
                {"name": "Client A", "score": 650, "plan": "Starter", "status": "Actioned", "commission": 100},
                {"name": "Client B", "score": 720, "plan": "Recovery", "status": "Paid", "commission": 100},
            ],
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_dsa_leads_persist(self):
        token = self._get_token()
        client.post("/api/dsa/leads",
            headers={"Authorization": f"Bearer {token}"},
            json=[{"name": "Persist Test", "score": 600}],
        )
        resp = client.get("/api/dsa/leads", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        leads = resp.json()
        assert len(leads) >= 1
        names = [l["name"] for l in leads]
        assert "Persist Test" in names

    def test_dsa_stats_after_leads(self):
        token = self._get_token()
        client.post("/api/dsa/leads",
            headers={"Authorization": f"Bearer {token}"},
            json=[
                {"name": "Stat A", "score": 600, "status": "Paid", "commission": 100},
                {"name": "Stat B", "score": 700, "status": "Actioned", "commission": 100},
            ],
        )
        resp = client.get("/api/dsa/stats", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        assert data["total_leads"] >= 2
        assert data["conversions"] >= 1

    def test_get_referral_link(self):
        token = self._get_token()
        resp = client.get("/api/dsa/referral-link", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "referral_code" in data
        assert data["referral_link"].startswith("https://clyr.in/ref/")

    def test_referral_link_idempotent(self):
        token = self._get_token()
        resp1 = client.get("/api/dsa/referral-link", headers={"Authorization": f"Bearer {token}"})
        resp2 = client.get("/api/dsa/referral-link", headers={"Authorization": f"Bearer {token}"})
        assert resp1.json()["referral_code"] == resp2.json()["referral_code"]

    def test_dsa_unauthenticated(self):
        resp = client.get("/api/dsa/stats")
        assert resp.status_code == 401
        resp = client.get("/api/dsa/leads")
        assert resp.status_code == 401
        resp = client.post("/api/dsa/leads", json=[{"name": "Test"}])
        assert resp.status_code == 401


# ─── Upload Tests ────────────────────────────────────────────────────────────

class TestUpload:
    def test_upload_non_pdf_rejected(self):
        resp = client.post("/api/upload", files={
            "file": ("test.txt", b"not a pdf", "text/plain")
        })
        assert resp.status_code == 400

    def test_upload_fake_pdf_rejected(self):
        """File with .pdf extension but wrong magic bytes is rejected."""
        resp = client.post("/api/upload", files={
            "file": ("test.pdf", b"not a real pdf content here and needs to be longer than 100 bytes to pass the size check but still not have pdf magic bytes at the start", "application/pdf")
        })
        assert resp.status_code == 400
        assert "not a valid pdf" in resp.json()["detail"].lower()

    def test_upload_oversized_rejected(self):
        big_content = b"%PDF" + b"x" * (11 * 1024 * 1024)
        resp = client.post("/api/upload", files={
            "file": ("big.pdf", big_content, "application/pdf")
        })
        assert resp.status_code == 413

    def test_upload_empty_rejected(self):
        resp = client.post("/api/upload", files={
            "file": ("empty.pdf", b"", "application/pdf")
        })
        assert resp.status_code == 400


# ─── Health Check ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}
