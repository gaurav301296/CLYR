"""
CLYR Full End-to-End Test
Starts the backend server and tests the complete pipeline with real HTTP requests.
"""
import os
import sys
import time
import json
import tempfile
import subprocess
import requests
import signal

sys.path.insert(0, r'C:\Users\shiva\Downloads\CLYR\backend')

# Load env
env_path = r'C:\Users\shiva\Downloads\CLYR\.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

BASE_URL = "http://localhost:8005"
OUTPUT_DIR = r'C:\Users\shiva\Downloads\CLYR\e2e_live_test'
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = {"total": 0, "passed": 0, "failed": 0, "errors": []}

def test(name, condition, error_msg=""):
    results["total"] += 1
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
# STEP 1: Start the backend server
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 1: Starting Backend Server")
print("=" * 70)

# Check if port 8005 is already in use
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8005))
sock.close()

if result == 0:
    print("  Port 8005 already in use. Using existing server.")
else:
    print("  Starting uvicorn server on port 8005...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=r'C:\Users\shiva\Downloads\CLYR\backend'
    )
    
    # Wait for server to start
    for i in range(30):
        time.sleep(1)
        try:
            resp = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if resp.status_code == 200:
                print(f"  Server started successfully (took {i+1}s)")
                break
        except:
            pass
        if i % 5 == 0:
            print(f"  Waiting for server... ({i+1}s)")
    else:
        print("  ERROR: Server failed to start within 30 seconds")
        try:
            server_proc.kill()
            stdout, stderr = server_proc.communicate(timeout=5)
            print(f"  STDOUT: {stdout.decode()[:500]}")
            print(f"  STDERR: {stderr.decode()[:500]}")
        except:
            pass
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Health Check
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 2: Health Check")
print("=" * 70)

try:
    resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
    test("Health endpoint returns 200", resp.status_code == 200)
    test("Health returns healthy status", resp.json() == {"status": "healthy"})
except Exception as e:
    test("Health check", False, str(e))

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Create test PDF and upload
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 3: Upload PDF → Generate Letter")
print("=" * 70)

# Create a realistic CIBIL report PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

test_pdf_path = os.path.join(OUTPUT_DIR, "test_cibil.pdf")

cibil_content = """
CIBIL TRANSCORE REPORT
REPORT DATE: 15-May-2026
CONSUMER NAME: Priya Sharma
DATE OF BIRTH: 22/08/1990
PAN: XYZPS5678G
CIBIL SCORE: 585

ACCOUNT 1: SBI CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
ACCOUNT NUMBER: XXXX-XXXX-XXXX-1234
SANCTIONED AMOUNT: 150,000 INR
CURRENT BALANCE: 1,20,000 INR
PAYMENT STATUS: OVERDUE
DPD (DAYS PAST DUE): 60 DAYS
REMARKS: WRITTEN OFF
DATE OPENED: 10/03/2020
DATE CLOSED: 15/01/2026

ACCOUNT 2: HDFC PERSONAL LOAN
ACCOUNT TYPE: INSTALMENT LOAN
ACCOUNT NUMBER: XXXX-XXXX-XXXX-5678
SANCTIONED AMOUNT: 500,000 INR
CURRENT BALANCE: 0 INR
PAYMENT STATUS: SETTLED
REMARKS: SETTLED FOR LESS THAN FULL AMOUNT
DATE OPENED: 05/06/2021
DATE CLOSED: 20/12/2024

ACCOUNT 3: ICICI BANK CREDIT CARD
ACCOUNT TYPE: REVOLVING CREDIT
ACCOUNT NUMBER: XXXX-XXXX-XXXX-9012
SANCTIONED AMOUNT: 200,000 INR
CURRENT BALANCE: 25,000 INR
PAYMENT STATUS: CURRENT
DPD: 0 DAYS
REMARKS: NO ADVERSE STATUS
DATE OPENED: 15/01/2023

ENQUIRIES:
1. HDFC BANK — 10/01/2026 — PERSONAL LOAN APPLICATION
2. SBI — 15/02/2026 — CREDIT CARD APPLICATION
3. ICICI BANK — 05/03/2026 — HOME LOAN APPLICATION
"""

doc = SimpleDocTemplate(test_pdf_path, pagesize=A4)
styles = getSampleStyleSheet()
story = []
for line in cibil_content.split('\n'):
    if line.strip():
        story.append(Paragraph(line.strip(), styles['Normal']))
        story.append(Spacer(1, 2))
doc.build(story)

test("Test PDF created", os.path.exists(test_pdf_path))

# Upload and get letter in Hindi
print("\n  Uploading PDF (Hindi)...")
with open(test_pdf_path, 'rb') as f:
    resp = requests.post(
        f"{BASE_URL}/api/upload?lang=hi",
        files={"file": ("cibil_report.pdf", f, "application/pdf")},
        timeout=60
    )

test("Upload returns 200", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

if resp.status_code == 200:
    data = resp.json()
    test("Response contains letter", "letter" in data)
    test("Score extracted correctly", data.get("score") == 585, f"Got {data.get('score')}")
    test("Name extracted", "Priya" in data.get("customer_name", ""), f"Got '{data.get('customer_name')}'")
    test("Language is Hindi", data.get("language") == "hi")
    
    letter = data.get("letter", "")
    test("Letter has GREETING", "GREETING:" in letter)
    test("Letter has INTRO", "INTRO:" in letter)
    test("Letter has ISSUE markers", "ISSUE #" in letter)
    test("Letter has ACTION markers", "ACTION:" in letter)
    test("Letter has SCORE_PROJECTION", "SCORE_PROJECTION:" in letter)
    test("Letter has CLOSING", "CLOSING:" in letter)
    test("Letter has DISPUTE_LETTERS", "DISPUTE_LETTERS:" in letter)
    test("Letter has Hindi script", any('\u0900' <= c <= '\u097F' for c in letter))
    test("Letter mentions SBI", "SBI" in letter)
    test("Letter mentions HDFC", "HDFC" in letter)
    test("Letter mentions Written Off", "WRITTEN OFF" in letter.upper())
    test("Letter mentions CIBIL dispute process", "cibil.com" in letter.lower() or "CIBIL" in letter)
    test("Letter mentions NOC", "NOC" in letter or "No Objection" in letter)
    test("Letter mentions RBI", "RBI" in letter or "rbi" in letter.lower())
    
    print(f"\n  Letter preview (first 500 chars):")
    print(f"  {'─' * 60}")
    for line in letter[:500].split('\n')[:15]:
        print(f"  {line}")
    print(f"  ...")
    print(f"  {'─' * 60}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Download letter as PDF
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 4: Download Letter as PDF")
print("=" * 70)

if resp.status_code == 200:
    data = resp.json()
    resp = requests.post(f"{BASE_URL}/api/download", json=data, timeout=30)
    
    test("Download returns 200", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")
    test("Content-Type is PDF", resp.headers.get("content-type") == "application/pdf")
    test("Has attachment header", "attachment" in resp.headers.get("content-disposition", ""))
    
    pdf_size = len(resp.content)
    test("PDF content > 2KB", pdf_size > 2000, f"Only {pdf_size} bytes")
    test("PDF has valid header", resp.content[:4] == b"%PDF")
    
    # Save the PDF
    pdf_path = os.path.join(OUTPUT_DIR, "priya_sharma_letter_hi.pdf")
    with open(pdf_path, 'wb') as f:
        f.write(resp.content)
    test("PDF saved to disk", os.path.exists(pdf_path))
    print(f"  PDF saved: {pdf_path} ({pdf_size} bytes)")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Test all languages via API
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 5: Test All Languages via API")
print("=" * 70)

languages = [
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

for lang_code, lang_name in languages:
    print(f"\n  [{lang_code}] {lang_name}:")
    try:
        with open(test_pdf_path, 'rb') as f:
            resp = requests.post(
                f"{BASE_URL}/api/upload?lang={lang_code}",
                files={"file": ("cibil_report.pdf", f, "application/pdf")},
                timeout=60
            )
        
        test(f"Upload {lang_name} returns 200", resp.status_code == 200, f"Got {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            test(f"Letter generated", len(data.get("letter", "")) > 100)
            test(f"Score correct", data.get("score") == 585)
            test(f"Language correct", data.get("language") == lang_code)
            
            # Download PDF
            resp = requests.post(f"{BASE_URL}/api/download", json=data, timeout=30)
            test(f"PDF download OK", resp.status_code == 200)
            test(f"PDF size > 2KB", len(resp.content) > 2000)
            
    except Exception as e:
        test(f"{lang_name} API test", False, str(e))

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Error handling
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STEP 6: Error Handling")
print("=" * 70)

# Invalid file type
resp = requests.post(
    f"{BASE_URL}/api/upload",
    files={"file": ("test.txt", b"not a pdf", "text/plain")},
    timeout=10
)
test("Invalid file type returns 400", resp.status_code == 400)

# Empty file
resp = requests.post(
    f"{BASE_URL}/api/upload",
    files={"file": ("test.pdf", b"", "application/pdf")},
    timeout=10
)
test("Empty file returns 400", resp.status_code == 400)

# Corrupt PDF
resp = requests.post(
    f"{BASE_URL}/api/upload",
    files={"file": ("test.pdf", b"not a pdf at all", "application/pdf")},
    timeout=10
)
test("Corrupt PDF returns 400", resp.status_code == 400)

# No file
resp = requests.post(f"{BASE_URL}/api/upload", timeout=10)
test("No file returns 422", resp.status_code == 422)

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("END-TO-END TEST SUMMARY")
print("=" * 70)
print(f"\nTotal Tests: {results['total']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success Rate: {results['passed']/max(results['total'],1)*100:.1f}%")

if results["errors"]:
    print(f"\nFailed Tests:")
    for err in results["errors"]:
        print(f"  ✗ {err}")

print(f"\nOutput files saved to: {OUTPUT_DIR}")
print("=" * 70)
