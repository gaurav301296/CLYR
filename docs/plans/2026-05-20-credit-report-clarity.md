# Credit Report Clarity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a full-stack, premium credit report clarity platform (CLYR) that processes complex CIBIL PDFs, generates plain Hinglish/English summaries, and displays an interactive dashboard and PDF download.

**Architecture:** A lightweight FastAPI python backend for PDF text extraction (pdfplumber), LLM-based parsing (OpenAI/Gemini), and report compilation (ReportLab), paired with a premium Vite + React frontend styled in custom vanilla CSS dark-mode glassmorphism.

**Tech Stack:** React 19, Vite, Vanilla CSS, Python 3.14, FastAPI, pdfplumber, ReportLab, pytest.

---

## Task 1: Project Initialization & Directory Structure

**Files:**
- Create: `README.md`
- Create: `.gitignore`

**Step 1: Write the initialization files**
Create the project root files detailing the structures.

**Step 2: Verify folder structure**
Ensure files are created successfully in the directory.

---

## Task 2: Backend Setup & PDF Extraction Utility

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/utils/parser.py`
- Create: `backend/tests/test_parser.py`

**Step 1: Write the failing test**
Create a test file `backend/tests/test_parser.py` that fails because the parser module is not yet implemented.

```python
import pytest
from app.utils.parser import extract_pdf_text

def test_extract_pdf_text_invalid_path():
    with pytest.raises(FileNotFoundError):
        extract_pdf_text("nonexistent_file.pdf")
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_parser.py`
Expected: Fail (ModuleNotFoundError)

**Step 3: Write minimal implementation**
Implement `backend/app/utils/parser.py` with basic path checking and pdfplumber extraction.

```python
import os
import pdfplumber

def extract_pdf_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_parser.py`
Expected: Pass

**Step 5: Commit changes**
Commit file updates.

---

## Task 3: Backend LLM Synthesis Service

**Files:**
- Create: `backend/app/services/llm_service.py`
- Create: `backend/tests/test_llm_service.py`

**Step 1: Write the failing test**
Create a test verifying the summary generator output format.

```python
import pytest
from app.services.llm_service import generate_credit_summary

def test_generate_credit_summary_empty():
    with pytest.raises(ValueError):
        generate_credit_summary("")
```

**Step 2: Run test to verify it fails**
Expected: Fail (ModuleNotFoundError)

**Step 3: Write minimal implementation**
Implement the service with robust prompts mapping the business blueprint rules (Hinglish/English plain breakdown, decision-focused: score, issues, action steps, timeline). If no LLM key is provided, default to a robust template ruleset.

```python
import os

def generate_credit_summary(raw_text: str) -> dict:
    if not raw_text or len(raw_text.strip()) == 0:
        raise ValueError("Text cannot be empty")
    
    # Mock / Fallback rules parsing if API key is not configured,
    # or actual API call to OpenAI / Gemini if configured.
    # Return structured dict containing score, issues, actions, timeline
    return {
        "score": 620,
        "customer_name": "Rajesh Kumar",
        "general_health": "Needs Attention (Medium Risk)",
        "issues": [
            {"account": "HDFC Credit Card", "type": "Red", "details": "Written Off amount of ₹45,000 in Feb 2025. This is blocking all future loan approvals.", "action": "Contact bank for Settlement letter / NOC. Pay the outstanding balance.", "impact": "High"},
            {"account": "SBI Personal Loan", "type": "Yellow", "details": "3 Late payments of 30+ days in the last 6 months. Signals inconsistent payment behavior.", "action": "Set up auto-debit and pay next 6 EMIs strictly on time.", "impact": "Medium"}
        ],
        "action_steps": [
            "Contact HDFC Card Division, negotiate a 'One-Time Settlement' (OTS) for HDFC card, and obtain NOC.",
            "Enable Auto-Debit on your SBI Current/Savings Account for SBI Personal Loan.",
            "Maintain Credit Card utilization below 30% on active cards."
        ],
        "timeline": [
            {"phase": "Month 1", "task": "Resolve HDFC Settlement, get payment receipt.", "status": "Critical"},
            {"phase": "Month 2-3", "task": "SBI loan active payment on-time, wait for CIBIL refresh (takes 45 days).", "status": "In Progress"},
            {"phase": "Month 6", "task": "Verify CIBIL score recovery progress. Simulated Score target: 720+.", "status": "Target"}
        ]
    }
```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_llm_service.py`
Expected: Pass

---

## Task 4: Backend ReportLab PDF Generation

**Files:**
- Create: `backend/app/utils/pdf_generator.py`
- Create: `backend/tests/test_pdf_generator.py`

**Step 1: Write the failing test**
Create a test to check that the PDF generator compiles a file.

```python
import os
import pytest
from app.utils.pdf_generator import create_report_pdf

def test_create_report_pdf_file_creation(tmp_path):
    output_path = os.path.join(tmp_path, "test_report.pdf")
    data = {
        "score": 620,
        "customer_name": "Rajesh Kumar",
        "general_health": "Needs Attention",
        "issues": [],
        "action_steps": [],
        "timeline": []
    }
    create_report_pdf(data, output_path)
    assert os.path.exists(output_path)
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_pdf_generator.py`
Expected: Fail

**Step 3: Write minimal implementation**
Implement ReportLab PDF generation with a premium design (matching the premium branding, clean table layout, color-coded badges for Red/Yellow/Green issues).

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_pdf_generator.py`
Expected: Pass

---

## Task 5: Backend API Endpoint Implementation

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

**Step 1: Write the failing test**
Create a test verifying the upload endpoint.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Step 2: Run test to verify it fails**
Expected: Fail

**Step 3: Write minimal implementation**
Build the FastAPI app with CORS, health check, PDF upload, parser trigger, LLM summary generation, and PDF download endpoints.

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_api.py`
Expected: Pass

---

## Task 6: Frontend Initialization & Layout Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/index.css`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/index.html`

**Step 1: Write boilerplate configuration**
Initialize Vite React app structure in the frontend directory. Use pure vanilla CSS in `index.css` to build a dark mode theme, using HSL colors, modern typography (Outfit/Inter), and styling tokens.

**Step 2: Verify compilation**
Run a local build `npm run build` or start local server.

---

## Task 7: Frontend Premium landing page & Pricing Selection

**Files:**
- Create: `frontend/src/components/LandingPage.jsx`
- Create: `frontend/src/components/LandingPage.css`

**Step 1: Build the landing page**
Implement a visual hero banner with glassmorphism layout, featuring details about the Credit report plain English summary for ₹499. Show a pricing card layout: Starter (₹499), Follow-up (₹799), Recovery Pack (₹1299).

**Step 2: Verify render**
Verify pages compile successfully.

---

## Task 8: Frontend File Uploader & Processing Animation

**Files:**
- Create: `frontend/src/components/Uploader.jsx`
- Create: `frontend/src/components/Uploader.css`

**Step 1: Build upload area**
Develop an interactive drag-and-drop file uploader accepting PDF files. Add a custom micro-animation displaying the progress: "Reading report data...", "Analyzing defaults...", "Formulating fix sequence...", "Generating PDF summary..."

**Step 2: Verify uploader state**
Verify animations and state updates occur correctly.

---

## Task 9: Frontend Interactive Dashboard & Score Simulator

**Files:**
- Create: `frontend/src/components/Dashboard.jsx`
- Create: `frontend/src/components/Dashboard.css`

**Step 1: Build the interactive dashboard**
Include:
- Credit Score gauge displaying current score (e.g. 620) and targets (e.g. 750).
- Issue breakdown: Red (Critical), Yellow (Medium), Green (Healthy) boxes.
- Action steps list (negotiate HDFC settlement, auto-debits, utilization limits).
- Credit repair simulator: Slider to simulate paying off defaults or late payments, updating the estimated future score dynamically.
- Download PDF report button.

**Step 2: Test dashboard rendering**
Ensure all sections render correctly with mock data.

---

## Task 10: Frontend Agent/DSA Portal

**Files:**
- Create: `frontend/src/components/AgentPortal.jsx`
- Create: `frontend/src/components/AgentPortal.css`

**Step 1: Build the DSA referral panel**
Display referral links, bulk PDF upload interface, client list tracker, and payout/commission calculators (₹100 payout per report converted to pay).

**Step 2: Verify portal interface**
Validate state transitions and calculations.
