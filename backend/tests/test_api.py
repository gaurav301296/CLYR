import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_no_file():
    response = client.post("/api/upload")
    assert response.status_code == 422


def test_upload_invalid_file_type():
    file_content = b"Not a PDF file content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_download_letter():
    """Test that the letter PDF generation works."""
    payload = {
        "letter": (
            "GREETING: Dear Test User,\n\n"
            "INTRO: Your score is 710 — this is decent but there's room to improve.\n\n"
            "ISSUE #1: HDFC Credit Card\n"
            "WHAT: High utilization at 94%\n"
            "IMPACT: This is costing you approximately 20-30 points\n"
            "ACTION: Pay down the balance below 30% utilization\n"
            "TIMELINE: 30 days\n"
            "SUCCESS_CHANCE: High\n\n"
            "SCORE_PROJECTION:\n"
            "Current: 710\n"
            "After fixing all issues: 740-760\n"
            "Timeline: 60 days\n\n"
            "CLOSING: You can do this! Start with the first step this week.\n\n"
            "DISPUTE_LETTERS:\n"
            "None needed for this issue."
        ),
        "language": "en",
        "score": 710,
        "customer_name": "Test User",
    }
    response = client.post("/api/download", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
