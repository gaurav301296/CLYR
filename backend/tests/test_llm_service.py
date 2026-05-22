import pytest
from app.services.llm_service import generate_credit_summary

def test_generate_credit_summary_empty():
    with pytest.raises(ValueError):
        generate_credit_summary("")

def test_generate_credit_summary_hdfc_default():
    report_text = """
    REPORT DATE: 2026-05-20
    CONSUMER NAME: Rajesh Kumar
    ACCOUNT 1: HDFC BANK CREDIT CARD
    ACCOUNT TYPE: REVOLVING CREDIT
    SANCTIONED AMOUNT: 200,000 INR
    CURRENT BALANCE: 1,45,000 INR
    PAYMENT STATUS: OVERDUE DPD 60 DAYS
    REMARKS: WRITTEN OFF
    """
    res = generate_credit_summary(report_text)
    assert res["customer_name"] == "Rajesh Kumar"
    assert len(res["issues"]) > 0
    issue = res["issues"][0]
    assert "HDFC Bank Credit Card" in issue["account"]
    assert "₹1,45,000" in issue["details"]
    assert "Red" in issue["type"]
