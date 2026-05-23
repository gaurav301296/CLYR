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
    # New format returns a letter string
    assert "letter" in res
    assert res["customer_name"] == "Rajesh Kumar"
    assert "HDFC" in res["letter"]
    assert "Rajesh Kumar" in res["letter"]


def test_generate_credit_summary_hindi():
    report_text = """
    REPORT DATE: 2026-05-20
    CONSUMER NAME: राजेश कुमार
    ACCOUNT 1: HDFC BANK CREDIT CARD
    ACCOUNT TYPE: REVOLVING CREDIT
    CURRENT BALANCE: 1,45,000 INR
    PAYMENT STATUS: OVERDUE
    REMARKS: WRITTEN OFF
    """
    res = generate_credit_summary(report_text, language="hi")
    assert "letter" in res
    assert res["language"] == "hi"
    # Letter should contain Hindi text
    assert "राजेश" in res["letter"] or "HDFC" in res["letter"]
