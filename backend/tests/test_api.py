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

def test_download_report():
    payload = {
        "score": 710,
        "customer_name": "Test User",
        "general_health": "Good",
        "issues": [
            {"account": "Card 1", "type": "Yellow", "details": "High limit usage", "action": "Pay it down", "impact": "Medium"}
        ],
        "action_steps": ["Pay card 1 balance down"],
        "timeline": [
            {"phase": "Month 1", "task": "Pay card", "status": "In Progress"}
        ]
    }
    response = client.post("/api/download", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
