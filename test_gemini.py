"""
Test with actual Gemini API — one language at a time with delays.
"""
import os
import sys
import time

sys.path.insert(0, r'C:\Users\shiva\Downloads\CLYR\backend')

env_path = r'C:\Users\shiva\Downloads\CLYR\.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

from app.services.llm_service import generate_credit_summary, clear_llm_cache

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

ENQUIRIES:
1. HDFC BANK — 15/01/2026 — CREDIT CARD APPLICATION
2. ICICI BANK — 10/02/2026 — PERSONAL LOAN APPLICATION
3. SBI — 05/03/2026 — HOME LOAN APPLICATION
4. AXIS BANK — 20/04/2026 — CREDIT CARD APPLICATION
"""

# Test Hindi with Gemini (most important market)
print("=" * 80)
print("TESTING HINDI (hi) WITH GEMINI API")
print("=" * 80)

clear_llm_cache()

try:
    result = generate_credit_summary(SAMPLE_REPORT, language="hi")
    letter = result.get("letter", "")
    
    print(f"\nLetter length: {len(letter)} chars")
    print(f"Language: {result.get('language', 'unknown')}")
    print(f"Score: {result.get('score', 'unknown')}")
    print(f"Customer: {result.get('customer_name', 'unknown')}")
    print(f"Used LLM: {result.get('raw_llm_output') is not None}")
    
    print(f"\n{'─' * 60}")
    print("FULL LETTER:")
    print(f"{'─' * 60}\n")
    print(letter)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Wait and test English
time.sleep(5)

print(f"\n\n{'=' * 80}")
print("TESTING ENGLISH (en) WITH GEMINI API")
print("=" * 80)

clear_llm_cache()

try:
    result = generate_credit_summary(SAMPLE_REPORT, language="en")
    letter = result.get("letter", "")
    
    print(f"\nLetter length: {len(letter)} chars")
    print(f"Used LLM: {result.get('raw_llm_output') is not None}")
    
    print(f"\n{'─' * 60}")
    print("FULL LETTER:")
    print(f"{'─' * 60}\n")
    print(letter)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
