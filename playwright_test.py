"""
CLYR Comprehensive SPA Test via Playwright — v2
Tests every feature in the live browser with correct selectors.
"""
import time, json, os, tempfile
from playwright.sync_api import sync_playwright
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_URL = "http://localhost:8005"
results = []

def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))

# Create test PDF
test_pdf = os.path.join(tempfile.gettempdir(), "test_cibil.pdf")
doc = SimpleDocTemplate(test_pdf, pagesize=A4)
styles = getSampleStyleSheet()
story = []
for line in [
    "CIBIL TRANSCORE REPORT", "REPORT DATE: 15-May-2026", "CONSUMER NAME: Priya Sharma",
    "CIBIL SCORE: 585", "", "ACCOUNT 1: SBI CREDIT CARD", "ACCOUNT TYPE: REVOLVING CREDIT",
    "SANCTIONED AMOUNT: 150,000 INR", "CURRENT BALANCE: 1,20,000 INR",
    "PAYMENT STATUS: OVERDUE", "DPD: 60 DAYS", "REMARKS: WRITTEN OFF", "",
    "ACCOUNT 2: HDFC PERSONAL LOAN", "ACCOUNT TYPE: INSTALMENT LOAN",
    "SANCTIONED AMOUNT: 500,000 INR", "CURRENT BALANCE: 0 INR",
    "PAYMENT STATUS: SETTLED", "REMARKS: SETTLED FOR LESS THAN FULL AMOUNT", "",
    "ACCOUNT 3: ICICI CREDIT CARD", "ACCOUNT TYPE: REVOLVING CREDIT",
    "SANCTIONED AMOUNT: 200,000 INR", "CURRENT BALANCE: 25,000 INR",
    "PAYMENT STATUS: CURRENT", "REMARKS: NO ADVERSE STATUS", "",
    "ENQUIRIES: 3 hard inquiries in last 6 months"
]:
    if line.strip():
        story.append(Paragraph(line.strip(), styles['Normal']))
        story.append(Spacer(1, 2))
doc.build(story)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    # ═══ TEST 1: Landing Page ═══
    print("\n=== TEST 1: Landing Page ===")
    page.goto(BASE_URL, timeout=30000)
    page.wait_for_timeout(5000)

    test("Page title", "CLYR" in page.title())
    test("Header brand", page.query_selector("text=CLYR") is not None)
    test("Home nav", page.query_selector("text=Home") is not None)
    test("Upload Report nav", page.query_selector("text=Upload Report") is not None)
    test("DSA Portal nav", page.query_selector("text=DSA Portal") is not None)
    test("Sign In button", page.query_selector("text=Sign In") is not None)
    test("Hero heading", page.query_selector("text=Your credit health, explained in plain English.") is not None)
    test("Hero subtitle", page.query_selector("text=Upload your confusing CIBIL") is not None)
    test("AI Bureau Parser feature", page.query_selector("text=AI Bureau Parser") is not None)
    test("Instant Dispute Scan feature", page.query_selector("text=Instant Dispute Scan") is not None)
    test("Recovery Roadmap feature", page.query_selector("text=Recovery Roadmap") is not None)
    test("Starter Pack", page.query_selector("text=Starter Pack") is not None)
    test("Follow-up Pack", page.query_selector("text=Follow-up Pack") is not None)
    test("Recovery Pack", page.query_selector("text=Recovery Pack") is not None)
    test("Price ₹499", page.query_selector("text=499") is not None)
    test("Price ₹799", page.query_selector("text=799") is not None)
    test("Price ₹1299", page.query_selector("text=1299") is not None)
    test("Language selector", page.query_selector("select") is not None)
    test("Footer disclaimer", page.query_selector("text=Disclaimer: CLYR is an educational tool") is not None)

    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\01_landing.png")

    # ═══ TEST 2: Language Switching ═══
    print("\n=== TEST 2: Language Switching ===")

    page.select_option("select", "hi")
    page.wait_for_timeout(3000)
    test("Hindi translation", page.query_selector("text=आपका क्रेडिट स्वास्थ्य") is not None)
    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\02_hindi.png")

    page.select_option("select", "ta")
    page.wait_for_timeout(3000)
    test("Tamil translation", page.query_selector("text=உங்கள் கிரெடிட்") is not None)

    page.select_option("select", "bn")
    page.wait_for_timeout(3000)
    test("Bengali translation", page.query_selector("text=আপনার ক্রেডিট") is not None)

    page.select_option("select", "en")
    page.wait_for_timeout(3000)

    # ═══ TEST 3: Upload Page ═══
    print("\n=== TEST 3: Upload Page ===")

    page.click("text=Upload Report")
    page.wait_for_timeout(3000)

    test("Upload page heading", page.query_selector("text=Upload Your Credit Report") is not None)
    test("Selected plan shown", page.query_selector("text=Starter Pack") is not None)
    test("Change Plan button", page.query_selector("text=Change Plan") is not None)
    test("Upload zone", page.query_selector("text=Drag & drop your credit report PDF here") is not None)
    test("Security note", page.query_selector("text=Safe & Secure") is not None)
    test("File input exists", page.query_selector("#pdf-upload") is not None)

    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\03_upload_page.png")

    # ═══ TEST 4: File Upload & Letter Generation ═══
    print("\n=== TEST 4: File Upload & Letter Generation ===")

    file_input = page.query_selector("#pdf-upload")
    if file_input:
        file_input.set_input_files(test_pdf)
        test("File selected", True)
    else:
        test("File selected", False, "File input not found")

    # Wait for loading state
    page.wait_for_timeout(3000)
    loading = page.query_selector("text=Analyzing") or page.query_selector("text=विश्लेषण") or page.query_selector("text=loading")
    test("Loading state appears", loading is not None)

    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\04_loading.png")

    # Wait for processing (up to 90s for Gemini API)
    print("  Waiting for letter generation (up to 90s)...")
    page.wait_for_timeout(90000)

    # Check for dashboard content
    score_el = page.query_selector("text=585")
    dashboard_el = page.query_selector("text=Credit Score Summary") or page.query_selector("text=Flagged Accounts") or page.query_selector("text=Score") or page.query_selector("text=स्कोर")
    test("Dashboard/letter content appears", score_el is not None or dashboard_el is not None)

    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\05_dashboard.png")

    # Get full page text for analysis
    full_text = page.evaluate("document.body.innerText")
    test("Letter contains score 585", "585" in full_text)
    test("Letter contains SBI", "SBI" in full_text or "sbi" in full_text.lower())
    test("Letter contains HDFC", "HDFC" in full_text or "hdfc" in full_text.lower())
    test("Letter contains issue details", "Written Off" in full_text or "WRITTEN OFF" in full_text)
    test("Letter contains action steps", "ACTION" in full_text or "action" in full_text.lower() or "करें" in full_text or "ये करें" in full_text)

    # ═══ TEST 5: Auth Flow ═══
    print("\n=== TEST 5: Authentication ===")

    page.goto(BASE_URL, timeout=30000)
    page.wait_for_timeout(5000)

    page.click("text=Sign In")
    page.wait_for_timeout(3000)

    auth_visible = page.query_selector("text=Create Account") or page.query_selector("text=Welcome Back")
    test("Auth modal appears", auth_visible is not None)

    if auth_visible:
        test_time = int(time.time())
        email_in = page.query_selector("input[type='email']")
        pass_in = page.query_selector("input[type='password']")
        name_in = page.query_selector("input[placeholder='Full Name']") or page.query_selector("input[type='text']")

        if email_in: email_in.fill(f"test_{test_time}@example.com")
        if pass_in: pass_in.fill("testpass123")
        if name_in: name_in.fill("Test User")

        create_btn = page.query_selector("text=Create Account")
        if create_btn:
            create_btn.click()
            page.wait_for_timeout(8000)

        sign_out = page.query_selector("text=Sign Out")
        test("Signup successful", sign_out is not None)

    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\06_auth.png")

    # ═══ TEST 6: DSA Portal ═══
    print("\n=== TEST 6: DSA Portal ===")

    page.goto(BASE_URL, timeout=30000)
    page.wait_for_timeout(5000)
    page.click("text=DSA Portal")
    page.wait_for_timeout(3000)

    dsa_visible = page.query_selector("text=DSA Portal") or page.query_selector("text=Partner") or page.query_selector("text=Referral")
    test("DSA Portal loads", dsa_visible is not None)
    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\07_dsa.png")

    # ═══ TEST 7: Mobile Responsive ═══
    print("\n=== TEST 7: Mobile Responsive ===")

    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(BASE_URL, timeout=30000)
    page.wait_for_timeout(5000)

    mobile_hero = page.query_selector("text=Your credit health")
    test("Mobile: Hero visible", mobile_hero is not None)
    page.screenshot(path=r"C:\Users\shiva\Downloads\CLYR\screenshots\08_mobile.png")

    page.set_viewport_size({"width": 1280, "height": 900})

    # ═══ SUMMARY ═══
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)
    rate = passed / max(total, 1) * 100

    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Rate: {rate:.1f}%")

    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ✗ {r['name']}: {r['detail']}")

    with open(r"C:\Users\shiva\Downloads\CLYR\playwright_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved.")

    browser.close()

if os.path.exists(test_pdf):
    os.unlink(test_pdf)
