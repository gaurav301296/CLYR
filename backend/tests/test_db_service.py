"""
Tests for CLYR database service.
Uses a temp file DB that's cleaned up per test.
"""
import os
import tempfile
import pytest

# Create a temp DB file before importing anything
_temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["CLYR_DB_PATH"] = _temp_db.name
os.environ["JWT_SECRET"] = "test-secret"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_placeholder"
os.environ["RAZORPAY_KEY_SECRET"] = "placeholder"
os.environ["SENTRY_DSN"] = ""
os.environ["OPENAI_API_KEY"] = "placeholder"

from app.services import db_service


@pytest.fixture(autouse=True)
def fresh_db():
    """Reinitialize DB for each test by removing and recreating."""
    # Close any existing connections by reinitializing
    db_service.init_db()
    yield
    # Clean up all data after each test
    db = db_service.get_db()
    try:
        db.execute("DELETE FROM security_log")
        db.execute("DELETE FROM dsa_referrals")
        db.execute("DELETE FROM dsa_leads")
        db.execute("DELETE FROM waitlist")
        db.execute("DELETE FROM orders")
        db.execute("DELETE FROM reports")
        db.execute("DELETE FROM refresh_tokens")
        db.execute("DELETE FROM users")
        db.commit()
    finally:
        db.close()


class TestReportOperations:
    def test_save_and_get_report(self):
        report_id = db_service.save_report(
            user_id="usr_test123",
            customer_name="Test User",
            score=720,
            language="en",
            letter_text="GREETING: Dear Test User",
            issues=[{"account": "HDFC", "type": "Yellow", "details": "Overdue", "action": "Pay now", "impact": "Medium", "amount": 50000}],
            general_health="Good",
        )
        assert report_id.startswith("rpt_")

        report = db_service.get_report_by_id(report_id)
        assert report is not None
        assert report["customer_name"] == "Test User"
        assert report["score"] == 720
        assert report["general_health"] == "Good"
        assert len(report["issues"]) == 1

    def test_get_user_reports(self):
        for i in range(3):
            db_service.save_report(
                user_id="usr_multi",
                customer_name=f"User {i}",
                score=650 + i * 50,
                language="en",
                letter_text=f"Letter {i}",
                issues=[],
            )

        reports = db_service.get_user_reports("usr_multi")
        assert len(reports) == 3
        assert reports[0]["customer_name"] == "User 2"

    def test_get_nonexistent_report(self):
        report = db_service.get_report_by_id("rpt_nonexistent")
        assert report is None

    def test_report_with_action_steps(self):
        report_id = db_service.save_report(
            user_id="usr_steps",
            customer_name="Steps User",
            score=600,
            language="en",
            letter_text="Letter",
            issues=[{"account": "SBI", "action": "Call bank"}],
            action_steps=["Step 1: Call bank", "Step 2: Get NOC"],
            timeline=[{"phase": "Phase 1", "task": "Call", "status": "Pending"}],
        )
        report = db_service.get_report_by_id(report_id)
        assert len(report["action_steps"]) == 2
        assert len(report["timeline"]) == 1


class TestOrderOperations:
    def test_create_order(self):
        order_id = db_service.create_order_record(
            user_id="usr_test",
            report_id="rpt_test",
            plan="Starter",
            amount=49900,
        )
        assert order_id.startswith("ord_")

    def test_update_order_payment(self):
        order_id = db_service.create_order_record(
            user_id="usr_test",
            report_id="rpt_test",
            plan="Recovery",
            amount=129900,
        )
        updated = db_service.update_order_payment(
            order_id=order_id,
            razorpay_payment_id="pay_123",
            razorpay_signature="sig_456",
        )
        assert updated is True

    def test_get_user_orders(self):
        for plan, amount in [("Starter", 49900), ("Follow-up", 79900)]:
            db_service.create_order_record(
                user_id="usr_orders",
                report_id="rpt_test",
                plan=plan,
                amount=amount,
            )
        orders = db_service.get_user_orders("usr_orders")
        assert len(orders) == 2


class TestWaitlistOperations:
    def test_add_to_waitlist(self):
        added = db_service.add_to_waitlist("wait@example.com")
        assert added is True

    def test_duplicate_waitlist(self):
        email = f"dup_{os.urandom(4).hex()}@example.com"
        db_service.add_to_waitlist(email)
        added = db_service.add_to_waitlist(email)
        assert added is False

    def test_waitlist_count(self):
        # Clean state from fixture
        count_before = db_service.get_waitlist_count()
        db_service.add_to_waitlist(f"count_{os.urandom(4).hex()}@example.com")
        assert db_service.get_waitlist_count() == count_before + 1


class TestDSAOperations:
    def test_save_and_get_leads(self):
        leads = [
            {"name": "Lead 1", "score": 600, "plan": "Starter", "status": "Actioned"},
            {"name": "Lead 2", "score": 750, "plan": "Recovery", "status": "Paid"},
        ]
        count = db_service.save_dsa_leads("usr_dsa", leads)
        assert count == 2

        fetched = db_service.get_dsa_leads("usr_dsa")
        assert len(fetched) == 2

    def test_dsa_stats(self):
        db_service.save_dsa_leads("usr_stats", [
            {"name": "A", "score": 600, "status": "Paid", "commission": 100},
            {"name": "B", "score": 700, "status": "Actioned", "commission": 100},
            {"name": "C", "score": 650, "status": "Paid", "commission": 100},
        ])
        stats = db_service.get_dsa_stats("usr_stats")
        assert stats["total_leads"] == 3
        assert stats["conversions"] == 2
        assert stats["total_commission"] == 300

    def test_referral_link(self):
        ref = db_service.get_or_create_referral("usr_ref")
        assert "referral_code" in ref
        assert "referral_link" in ref
        assert ref["referral_link"].startswith("https://clyr.in/ref/")

    def test_referral_link_idempotent(self):
        uid = f"usr_ref_{os.urandom(4).hex()}"
        ref1 = db_service.get_or_create_referral(uid)
        ref2 = db_service.get_or_create_referral(uid)
        assert ref1["referral_code"] == ref2["referral_code"]


class TestSecurityLog:
    def test_log_event(self):
        db_service.log_security_event("test_event", user_id="usr_test", details="test")
