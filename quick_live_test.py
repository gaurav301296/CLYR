"""Quick live test against running server."""
import os, sys, json, time, tempfile, requests

BASE_URL = "http://localhost:8005"
OUTPUT_DIR = r'C:\Users\shiva\Downloads\CLYR\e2e_live_test'
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = {"total": 0, "passed": 0, "failed": 0, "errors": []}

def test(name, condition, error_msg=""):
    results["total"] += 1
    if condition:
        results["passed"] += 1
        print(f"  ✓ {name}")
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {error_msg}")
        print(f"  ✗ {name} — {error_msg}")

# Create test PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

test_pdf = os.path.join(OUTPUT_DIR, "test.pdf")
doc = SimpleDocTemplate(test_pdf, pagesize=A4)
styles = getSampleStyleSheet()
story = []
content = """CIBIL TRANSCORE REPORT
REPORT DATE: 15-May-2026
CONSUMER NAME: Priya Sharma
CIBIL SCORE: 585

ACCOUNT 1: SBI CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
SANCTIONED AMOUNT: 150,000 INR
CURRENT BALANCE: 1,20,000 INR
PAYMENT STATUS: OVERDUE
DPD: 60 DAYS
REMARKS: WRITTEN OFF

ACCOUNT 2: HDFC PERSONAL LOAN
ACCOUNT TYPE: INSTALMENT LOAN
SANCTIONED AMOUNT: 500,000 INR
CURRENT BALANCE: 0 INR
PAYMENT STATUS: SETTLED
REMARKS: SETTLED FOR LESS THAN FULL AMOUNT

ACCOUNT 3: ICICI CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
SANCTIONED AMOUNT: 200,000 INR
CURRENT BALANCE: 25,000 INR
PAYMENT STATUS: CURRENT
REMARKS: NO ADVERSE STATUS

ENQUIRIES: 3"""
for line in content.split('\n'):
    if line.strip():
        story.append(Paragraph(line.strip(), styles['Normal']))
        story.append(Spacer(1, 2))
doc.build(story)

# Health check
print("=== HEALTH CHECK ===")
r = requests.get(f"{BASE_URL}/api/health", timeout=5)
test("Health 200", r.status_code == 200)
test("Healthy", r.json() == {"status": "healthy"})

# Upload Hindi
print("\n=== UPLOAD (Hindi) ===")
with open(test_pdf, 'rb') as f:
    r = requests.post(f"{BASE_URL}/api/upload?lang=hi", files={"file": ("test.pdf", f, "application/pdf")}, timeout=120)
test("Upload 200", r.status_code == 200, f"Got {r.status_code}: {r.text[:300]}")

if r.status_code == 200:
    data = r.json()
    letter = data.get("letter", "")
    test("Has letter", "letter" in data)
    test("Score 585", data.get("score") == 585)
    test("Name Priya", "Priya" in data.get("customer_name", ""))
    test("Lang hi", data.get("language") == "hi")
    test("GREETING:", "GREETING:" in letter)
    test("INTRO:", "INTRO:" in letter)
    test("ISSUE #", "ISSUE #" in letter)
    test("ACTION:", "ACTION:" in letter)
    test("SCORE_PROJECTION:", "SCORE_PROJECTION:" in letter)
    test("CLOSING:", "CLOSING:" in letter)
    test("DISPUTE_LETTERS:", "DISPUTE_LETTERS:" in letter)
    test("Hindi script", any('\u0900' <= c <= '\u097F' for c in letter))
    test("Mentions SBI", "SBI" in letter)
    test("Mentions HDFC", "HDFC" in letter)
    test("Mentions NOC", "NOC" in letter or "No Objection" in letter)
    test("Mentions RBI", "RBI" in letter or "rbi" in letter.lower())
    test("Mentions cibil.com", "cibil.com" in letter.lower())
    
    print(f"\nLetter length: {len(letter)} chars")
    print(f"First 600 chars:\n{letter[:600]}")
    
    # Download PDF
    print("\n=== DOWNLOAD PDF ===")
    r = requests.post(f"{BASE_URL}/api/download", json=data, timeout=30)
    test("Download 200", r.status_code == 200)
    test("PDF content-type", r.headers.get("content-type") == "application/pdf")
    test("PDF size > 2KB", len(r.content) > 2000, f"Got {len(r.content)} bytes")
    test("PDF header", r.content[:4] == b"%PDF")
    
    pdf_path = os.path.join(OUTPUT_DIR, "priya_hi.pdf")
    with open(pdf_path, 'wb') as f:
        f.write(r.content)
    print(f"PDF saved: {pdf_path} ({len(r.content)} bytes)")

# Test all languages quickly
print("\n=== ALL LANGUAGES ===")
for lang, name in [("en","English"),("hi","Hindi"),("bn","Bengali"),("te","Telugu"),("mr","Marathi"),("ta","Tamil"),("gu","Gujarati"),("kn","Kannada"),("ml","Malayalam"),("pa","Punjabi")]:
    with open(test_pdf, 'rb') as f:
        r = requests.post(f"{BASE_URL}/api/upload?lang={lang}", files={"file": ("test.pdf", f, "application/pdf")}, timeout=120)
    ok = r.status_code == 200 and "letter" in r.json()
    test(f"{name} ({lang})", ok, f"status={r.status_code}")
    if ok:
        letter = r.json().get("letter", "")
        has_issue = "ISSUE #" in letter
        has_action = "ACTION:" in letter
        has_closing = "CLOSING:" in letter
        print(f"  → {len(letter)} chars | Issues: {'✓' if has_issue else '✗'} | Actions: {'✓' if has_action else '✗'} | Closing: {'✓' if has_closing else '✗'}")

# Error cases
print("\n=== ERROR CASES ===")
r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("t.txt", b"nope", "text/plain")}, timeout=10)
test("Bad file type → 400", r.status_code == 400)
r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("t.pdf", b"", "application/pdf")}, timeout=10)
test("Empty file → 400", r.status_code == 400)
r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("t.pdf", b"fake", "application/pdf")}, timeout=10)
test("Fake PDF → 400", r.status_code == 400)
r = requests.post(f"{BASE_URL}/api/upload", timeout=10)
test("No file → 422", r.status_code == 422)

# Summary
print(f"\n{'='*60}")
print(f"RESULTS: {results['passed']}/{results['total']} passed ({results['passed']/max(results['total'],1)*100:.1f}%)")
if results["errors"]:
    print("Failures:")
    for e in results["errors"]:
        print(f"  ✗ {e}")
print(f"Output: {OUTPUT_DIR}")
