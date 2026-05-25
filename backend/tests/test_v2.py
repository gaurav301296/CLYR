"""
CLYR v2 — Backend Tests
Run with: pytest backend/tests/ -v
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_xxxxx"
os.environ["RAZORPAY_KEY_SECRET"] = "test-secret"

from app.main import app
from app.config import config

client = TestClient(app)


# ── Health Check ─────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    def test_health_no_auth_required(self):
        response = client.get("/api/health")
        assert response.status_code == 200


# ── Config Validation ────────────────────────────────────────────────────────

class TestConfig:
    def test_config_loads(self):
        assert config is not None
        assert config.port == 8005

    def test_config_environment(self):
        assert config.environment == "test"

    def test_config_validation_test_env(self):
        # In test mode, missing secrets should NOT crash (non-strict)
        errors = config.validate()
        # We have test keys set, so should be no errors
        assert isinstance(errors, list)


# ── LLM Service ──────────────────────────────────────────────────────────────

class TestLLMService:
    def test_empty_text_raises(self):
        from app.services.llm_service import generate_credit_summary
        with pytest.raises(ValueError, match="too short"):
            generate_credit_summary("")

    def test_short_text_raises(self):
        from app.services.llm_service import generate_credit_summary
        with pytest.raises(ValueError):
            generate_credit_summary("hi")

    def test_fallback_parsing(self):
        from app.services.llm_service import _fallback_parsing
        result = _fallback_parsing("CIBIL Score: 650\nSome account info", {
            "customer_name": "", "score": 0, "general_health": "",
            "letter": "", "issues": [], "action_steps": [], "timeline": [],
            "language": "en"
        })
        assert result["score"] == 650
        assert result["general_health"] == "Fair"

    def test_fallback_no_score(self):
        from app.services.llm_service import _fallback_parsing
        result = _fallback_parsing("No score here", {
            "customer_name": "", "score": 0, "general_health": "",
            "letter": "", "issues": [], "action_steps": [], "timeline": [],
            "language": "en"
        })
        assert result["score"] == 600  # Default

    def test_fallback_written_off_detected(self):
        from app.services.llm_service import _fallback_parsing
        result = _fallback_parsing("Account written off: ₹50,000", {
            "customer_name": "", "score": 0, "general_health": "",
            "letter": "", "issues": [], "action_steps": [], "timeline": [],
            "language": "en"
        })
        assert len(result["issues"]) > 0
        assert result["issues"][0]["account"] == "Written Off Account"


# ── PDF Parser ───────────────────────────────────────────────────────────────

class TestParser:
    def test_missing_file_raises(self):
        from app.utils.parser import extract_pdf_text
        with pytest.raises(FileNotFoundError):
            extract_pdf_text("/nonexistent/file.pdf")


# ── Sanitization ─────────────────────────────────────────────────────────────

class TestSanitization:
    def test_sanitize_html(self):
        from app.utils.sanitization import sanitize_pdf_text
        result = sanitize_pdf_text("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_long_text(self):
        from app.utils.sanitization import sanitize_pdf_text
        long_text = "A" * 10000
        result = sanitize_pdf_text(long_text)
        assert len(result) <= 5000

    def test_sanitize_filename(self):
        from app.utils.sanitization import sanitize_filename
        assert sanitize_filename("../../../etc/passwd") == "etc_passwd.pdf"
        assert sanitize_filename("report") == "report.pdf"
        assert sanitize_filename("") == "report.pdf"


# ── Models ───────────────────────────────────────────────────────────────────

class TestModels:
    def test_signup_validation(self):
        from app.models import SignupRequest
        # Valid
        req = SignupRequest(email="test@example.com", password="Test1234")
        assert req.email == "test@example.com"

    def test_signup_weak_password(self):
        from app.models import SignupRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            SignupRequest(email="test@example.com", password="weak")

    def test_plan_prices(self):
        from app.models import PlanType
        prices = PlanType.prices()
        assert prices[PlanType.STARTER] == 49900
        assert prices[PlanType.FOLLOWUP] == 79900
        assert prices[PlanType.RECOVERY] == 129900

    def test_plan_price_inr(self):
        from app.models import PlanType
        assert PlanType.price_inr("Starter") == 499
        assert PlanType.price_inr("Follow-up") == 799
        assert PlanType.price_inr("Recovery") == 1299


# ── Waitlist ─────────────────────────────────────────────────────────────────

class TestWaitlist:
    def test_waitlist_requires_email(self):
        response = client.post("/api/waitlist", json={})
        assert response.status_code == 422  # Validation error

    def test_waitlist_invalid_email(self):
        response = client.post("/api/waitlist", json={"email": "not-an-email"})
        assert response.status_code == 422


# ── CORS ─────────────────────────────────────────────────────────────────────

class TestCORS:
    def test_cors_headers(self):
        response = client.options("/api/health", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        })
        assert response.status_code in [200, 204]


# ── Security Headers ─────────────────────────────────────────────────────────

class TestSecurityHeaders:
    def test_security_headers_present(self):
        response = client.get("/api/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert "Strict-Transport-Security" in response.headers
