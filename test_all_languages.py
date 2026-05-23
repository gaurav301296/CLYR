"""
Test CLYR letter generation in all 10 languages with a realistic sample report.
"""
import os
import sys
import json

# Setup path
sys.path.insert(0, r'C:\Users\shiva\Downloads\CLYR\backend')

# Load env vars from .env file
env_path = r'C:\Users\shiva\Downloads\CLYR\.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

from app.services.llm_service import generate_credit_summary

# Realistic sample CIBIL report text
SAMPLE_REPORT = """
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

ACCOUNT 4: PERSONAL LOAN — BAJAJ FINANCE
ACCOUNT TYPE: INSTALMENT LOAN
ACCOUNT NUMBER: XXXX-XXXX-XXXX-5566
SANCTIONED AMOUNT: 100,000 INR
CURRENT BALANCE: 0 INR
PAYMENT STATUS: CLOSED
REMARKS: REGULAR CLOSURE
DATE OPENED: 05/09/2022
DATE CLOSED: 20/04/2025

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

print("=" * 80)
print("CLYR LETTER GENERATION — ALL 10 LANGUAGES")
print("=" * 80)
print(f"\nSample Report: Rajesh Kumar, Score: 540")
print(f"Issues: HDFC card written off (₹1,85,000), SBI loan settled, 4 hard enquiries")
print("=" * 80)

results = {}

for lang_code, lang_name in LANGUAGES:
    print(f"\n{'─' * 60}")
    print(f"  {lang_name} ({lang_code})")
    print(f"{'─' * 60}")
    
    try:
        result = generate_credit_summary(SAMPLE_REPORT, language=lang_code)
        letter = result.get("letter", "")
        
        # Print first 600 chars of the letter
        preview = letter[:600] + "..." if len(letter) > 600 else letter
        print(preview)
        
        # Store for analysis
        results[lang_code] = {
            "name": lang_name,
            "letter_length": len(letter),
            "has_greeting": "GREETING" in letter or any(g in letter for g in ["Dear", "जी", "জী", "గారు", "அவர்களே", "ಅವರೆ", "അവർകൾ"]),
            "has_issues": "ISSUE" in letter or "समस्यা" in letter or "সমস্যা" in letter or "సమస్య" in letter or "பிரச்சனை" in letter or "ಸಮಸ್ಯೆ" in letter or "പ്രശ്നം" in letter or "ਸਮੱਸਿਆ" in letter,
            "has_action": "ACTION" in letter or "करें" in letter or "করুন" in letter or "చేయండి" in letter or "செய்யுங்கள்" in letter or "ಮಾಡಿ" in letter or "ചെയ്യുക" in letter or "ਕਰੋ" in letter,
            "has_score_projection": "SCORE_PROJECTION" in letter or "स्कोर" in letter or "স্কোর" in letter or "స్కోర్" in letter or "ஸ்கோர்" in letter or "ಸ್ಕೋರ್" in letter or "സ്കോർ" in letter or "ਸਕੋਰ" in letter,
        }
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results[lang_code] = {"name": lang_name, "error": str(e)}

# Summary
print(f"\n{'=' * 80}")
print("SUMMARY")
print(f"{'=' * 80}")
print(f"{'Language':<15} {'Code':<6} {'Length':<10} {'Greeting':<10} {'Issues':<10} {'Action':<10} {'Score':<10}")
print(f"{'─' * 71}")
for lang_code, info in results.items():
    if "error" in info:
        print(f"{info['name']:<15} {lang_code:<6} ERROR: {info['error'][:40]}")
    else:
        print(f"{info['name']:<15} {lang_code:<6} {info['letter_length']:<10} "
              f"{'✓' if info['has_greeting'] else '✗':<10} "
              f"{'✓' if info['has_issues'] else '✗':<10} "
              f"{'✓' if info['has_action'] else '✗':<10} "
              f"{'✓' if info['has_score_projection'] else '✗':<10}")
