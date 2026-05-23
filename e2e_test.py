"""
CLYR End-to-End Test Suite
Tests the complete pipeline: PDF upload → Letter generation → PDF download
"""
import os
import sys
import json
import time
import tempfile
import requests

sys.path.insert(0, r'C:\Users\shiva\Downloads\CLYR\backend')

# Load env
env_path = r'C:\Users\shiva\Downloads\CLYR\.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

from app.utils.parser import extract_pdf_text
from app.services.llm_service import generate_credit_summary
from app.utils.pdf_generator import create_letter_pdf

# Create a realistic sample CIBIL report as text (simulating PDF extraction)
SAMPLE_CIBIL_REPORT = """
CIBIL TRANSCORE REPORT
REPORT DATE: 15-May-2026
CONSUMER NAME: Rajesh Kumar
DATE OF BIRTH: 12/03/1988
PAN: ABCPK1234F
CIBIL SCORE: 540

ACCOUNT 1: HDFC BANK CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
ACCOUNT NUMBER: XXXX-XXXX-XXXX-4521
SANCTIONED AMOUNT: 200,000 INR
CURRENT BALANCE: 1,85,000 INR
PAYMENT STATUS: OVERDUE
DPD (DAYS PAST DUE): 90 DAYS
REMARKS: WRITTEN OFF
DATE OPENED: 15/06/2019
DATE CLOSED: 20/01/2025

ACCOUNT 2: SBI PERSONAL LOAN
ACCOUNT TYPE: INSTALMENT LOAN
ACCOUNT NUMBER: XXXX-XXXX-XXXX-7891
SANCTIONED AMOUNT: 300,000 INR
CURRENT BALANCE: 0 INR
PAYMENT STATUS: SETTLED
REMARKS: SETTLED FOR LESS THAN FULL AMOUNT
DATE OPENED: 10/01/2020
DATE CLOSED: 15/08/2024

ACCOUNT 3: ICICI BANK CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
ACCOUNT NUMBER: XXXX-XXXX-XXXX-3344
SANCTIONED AMOUNT: 150,000 INR
CURRENT BALANCE: 45,000 INR
PAYMENT STATUS: CURRENT
DPD: 0 DAYS
REMARKS: NO ADVERSE STATUS
DATE OPENED: 22/03/2021

ENQUIRIES:
1. HDFC BANK — 15/01/2026 — CREDIT CARD APPLICATION
2. ICICI BANK — 10/02/2026 — PERSONAL LOAN APPLICATION
3. SBI — 05/03/2026 — HOME LOAN APPLICATION
4. AXIS BANK — 20/04/2026 — CREDIT CARD APPLICATION
"""

LANGUAGES = [
    ("en", "English"),
    ("hi", "Hindi"),
    ("bn", "Bengali"),
    ("te", "Telugu"),
    ("mr", "Marathi"),
    ("ta", "Tamil"),
    ("gu", "Gujarati"),
    ("kn", "Kannada"),
    ("ml", "Malayalam"),
    ("pa", "Punjabi"),
]

OUTPUT_DIR = r'C:\Users\shiva\Downloads\CLYR\e2e_test_output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "language_results": {},
}

def test(name, condition, error_msg=""):
    results["total_tests"] += 1
    if condition:
        results["passed"] += 1
        print(f"  ✓ {name}")
        return True
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {error_msg}")
        print(f"  ✗ {name} — {error_msg}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: PDF Parser
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST 1: PDF Parser")
print("=" * 70)

# Create a test PDF file
test_pdf_path = os.path.join(OUTPUT_DIR, "test_cibil_report.pdf")
try:
    # Use reportlab to create a test PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    doc = SimpleDocTemplate(test_pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    for line in SAMPLE_CIBIL_REPORT.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), styles['Normal']))
            story.append(Spacer(1, 2))
    
    doc.build(story)
    test("PDF file created", os.path.exists(test_pdf_path))
    
    # Test PDF text extraction
    extracted_text = extract_pdf_text(test_pdf_path)
    test("PDF text extracted", len(extracted_text) > 100, f"Only {len(extracted_text)} chars extracted")
    test("Score found in extracted text", "540" in extracted_text)
    test("HDFC account found", "HDFC" in extracted_text)
    test("SBI account found", "SBI" in extracted_text)
    test("Written off status found", "WRITTEN OFF" in extracted_text.upper())
    
except Exception as e:
    test("PDF creation/parsing", False, str(e))

# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Letter Generation — All Languages
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST 2: Letter Generation — All 10 Languages")
print("=" * 70)

for lang_code, lang_name in LANGUAGES:
    print(f"\n  [{lang_code}] {lang_name}:")
    try:
        result = generate_credit_summary(SAMPLE_CIBIL_REPORT, language=lang_code)
        
        letter = result.get("letter", "")
        score = result.get("score", 0)
        name = result.get("customer_name", "")
        
        test(f"Letter generated", len(letter) > 100, f"Only {len(letter)} chars")
        test(f"Score extracted correctly", score == 540, f"Got {score}")
        test(f"Name extracted", "Rajesh" in name, f"Got '{name}'")
        test(f"Has greeting", any(g in letter for g in ["Dear", "जी", "জী", "గారు", "அவர்களே", "ಅವರೆ", "അവർകൾ", "ਜੀ"]))
        test(f"Has issues section", "ISSUE" in letter or "समस्या" in letter or "সমস্যা" in letter or "సమస్య" in letter or "பிரச்சனை" in letter or "ಸಮಸ್ಯೆ" in letter or "പ്രശ്നം" in letter or "ਸਮੱਸਿਆ" in letter)
        test(f"Has action steps", "ACTION" in letter or "करें" in letter or "করুন" in letter or "చేయండి" in letter or "செய்யுங்கள்" in letter or "ಮಾಡಿ" in letter or "ചെയ്യുക" in letter or "ਕਰੋ" in letter)
        test(f"Has score projection", "SCORE_PROJECTION" in letter or "स्कोर" in letter or "স্কোর" in letter or "స్కోర్" in letter or "ஸ்கோர்" in letter or "ಸ್ಕೋರ್" in letter or "സ്കോർ" in letter or "ਸਕੋਰ" in letter)
        test(f"Has closing", "CLOSING" in letter or "— CLYR" in letter)
        
        # Check for specific vernacular content
        if lang_code == "hi":
            test(f"Hindi greeting format", "जी" in letter)
            test(f"Hindi action words", "करें" in letter or "भर" in letter)
        elif lang_code == "ta":
            test(f"Tamil greeting format", "அவர்களே" in letter)
            test(f"Tamil action words", "செய்யுங்கள்" in letter)
        elif lang_code == "bn":
            test(f"Bengali greeting format", "জী" in letter)
            test(f"Bengali action words", "করুন" in letter)
        
        results["language_results"][lang_code] = {
            "name": lang_name,
            "letter_length": len(letter),
            "score": score,
            "name_extracted": name,
            "status": "PASS"
        }
        
    except Exception as e:
        test(f"{lang_name} letter generation", False, str(e))
        results["language_results"][lang_code] = {"name": lang_name, "status": "FAIL", "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: PDF Generation — All Languages
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST 3: PDF Generation — All 10 Languages")
print("=" * 70)

for lang_code, lang_name in LANGUAGES:
    print(f"\n  [{lang_code}] {lang_name}:")
    try:
        result = generate_credit_summary(SAMPLE_CIBIL_REPORT, language=lang_code)
        
        pdf_data = {
            "letter": result.get("letter", ""),
            "language": lang_code,
            "score": result.get("score", 540),
            "customer_name": result.get("customer_name", "Rajesh Kumar"),
        }
        
        pdf_path = os.path.join(OUTPUT_DIR, f"letter_{lang_code}.pdf")
        create_letter_pdf(pdf_data, pdf_path)
        
        test(f"PDF file created", os.path.exists(pdf_path))
        
        file_size = os.path.getsize(pdf_path)
        test(f"PDF size > 1KB", file_size > 1000, f"Only {file_size} bytes")
        test(f"PDF size > 2KB (with fonts)", file_size > 2000, f"Only {file_size} bytes")
        
        # Verify it's a valid PDF
        with open(pdf_path, 'rb') as f:
            header = f.read(4)
        test(f"Valid PDF header", header == b"%PDF", f"Header: {header}")
        
    except Exception as e:
        test(f"{lang_name} PDF generation", False, str(e))

# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: API Endpoints (Direct function calls)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST 4: API Endpoints (Direct)")
print("=" * 70)

# Test health check
try:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Health check
    resp = client.get("/api/health")
    test("Health check returns 200", resp.status_code == 200)
    test("Health check returns healthy", resp.json() == {"status": "healthy"})
    
    # Upload endpoint
    with open(test_pdf_path, 'rb') as f:
        resp = client.post("/api/upload", files={"file": ("test.pdf", f, "application/pdf")}, params={"lang": "hi"})
    
    test("Upload returns 200", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")
    
    if resp.status_code == 200:
        data = resp.json()
        test("Upload returns letter", "letter" in data)
        test("Upload returns score", data.get("score") == 540)
        test("Upload returns name", "Rajesh" in data.get("customer_name", ""))
        
        # Download endpoint
        resp = client.post("/api/download", json=data)
        test("Download returns 200", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")
        test("Download returns PDF", resp.headers.get("content-type") == "application/pdf")
        test("Download has attachment", "attachment" in resp.headers.get("content-disposition", ""))
        
        # Save the downloaded PDF
        download_path = os.path.join(OUTPUT_DIR, "downloaded_letter.pdf")
        with open(download_path, 'wb') as f:
            f.write(resp.content)
        test("Downloaded PDF saved", os.path.exists(download_path))
        test("Downloaded PDF > 2KB", os.path.getsize(download_path) > 2000)
    
    # Test with different languages
    for lang_code, lang_name in [("en", "English"), ("hi", "Hindi"), ("ta", "Tamil")]:
        with open(test_pdf_path, 'rb') as f:
            resp = client.post("/api/upload", files={"file": ("test.pdf", f, "application/pdf")}, params={"lang": lang_code})
        test(f"Upload {lang_name} ({lang_code})", resp.status_code == 200, f"Got {resp.status_code}")
    
    # Test error cases
    # Invalid file type
    resp = client.post("/api/upload", files={"file": ("test.txt", b"not a pdf", "text/plain")})
    test("Invalid file type returns 400", resp.status_code == 400)
    
    # Empty file
    resp = client.post("/api/upload", files={"file": ("test.pdf", b"", "application/pdf")})
    test("Empty file returns 400", resp.status_code == 400)
    
    # Corrupt PDF
    resp = client.post("/api/upload", files={"file": ("test.pdf", b"not a pdf at all", "application/pdf")})
    test("Corrupt PDF returns 400", resp.status_code == 400)
    
except Exception as e:
    test("API endpoint tests", False, str(e))
    import traceback
    traceback.print_exc()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Content Quality Checks
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST 5: Content Quality Checks")
print("=" * 70)

try:
    result = generate_credit_summary(SAMPLE_CIBIL_REPORT, language="hi")
    letter = result.get("letter", "")
    
    # Check for specific content
    test("Mentions HDFC", "HDFC" in letter)
    test("Mentions SBI", "SBI" in letter)
    test("Mentions Written Off", "WRITTEN OFF" in letter or "written off" in letter.lower())
    test("Mentions Settled", "SETTLED" in letter or "settled" in letter.lower())
    test("Has score 540", "540" in letter)
    
    # Check for action steps
    test("Has CIBIL reference", "CIBIL" in letter or "cibil" in letter.lower())
    test("Has NOC reference", "NOC" in letter or "No Objection" in letter)
    test("Has dispute reference", "dispute" in letter.lower() or "विवाद" in letter)
    
    # Check for vernacular quality
    test("Has Hindi script", any('\u0900' <= c <= '\u097F' for c in letter))  # Devanagari range
    test("Has Indian numbering", "₹" in letter or "रु" in letter)
    
    # Check letter structure
    test("Has greeting section", "GREETING:" in letter or "जी" in letter)
    test("Has intro section", "INTRO:" in letter)
    test("Has issue sections", "ISSUE #" in letter or "समस्या #" in letter)
    test("Has closing section", "CLOSING:" in letter or "— CLYR" in letter)
    
except Exception as e:
    test("Content quality checks", False, str(e))

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("END-TO-END TEST SUMMARY")
print("=" * 70)
print(f"\nTotal Tests: {results['total_tests']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success Rate: {results['passed']/max(results['total_tests'],1)*100:.1f}%")

if results["errors"]:
    print(f"\nFailed Tests:")
    for err in results["errors"]:
        print(f"  ✗ {err}")

print(f"\nLanguage Results:")
for lang_code, info in results["language_results"].items():
    status = info.get("status", "UNKNOWN")
    length = info.get("letter_length", 0)
    print(f"  {info.get('name', lang_code)} ({lang_code}): {status} ({length} chars)")

print(f"\nOutput files saved to: {OUTPUT_DIR}")
print("=" * 70)
