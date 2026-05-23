import os
import pytest
from app.utils.pdf_generator import create_letter_pdf


def test_create_letter_pdf_file_creation(tmp_path):
    output_path = os.path.join(tmp_path, "test_letter.pdf")
    data = {
        "letter": "GREETING: राजेश जी,\n\nINTRO: आपका स्कोर 620 है — इसमें सुधार चाहिए।\n\nISSUE #1: HDFC क्रेडिट कार्ड\nWHAT: ₹45,000 का Written Off दिख रहा है\nIMPACT: इससे स्कोर 40-50 अंक कम है\nACTION: HDFC बैंक से NOC लें और CIBIL पर dispute करें\nTIMELINE: 30-45 दिन\nSUCCESS_CHANCE: High\n\nSCORE_PROJECTION:\nCurrent: 620\nAfter fixing all issues: 660-680\nTimeline: 90 दिन\n\nCLOSING: चिंता न करें, ये ठीक हो सकता है।\n\nDISPUTE_LETTERS:\nTo: HDFC Bank\nSubject: Request for NOC\nDear Sir, ...",
        "language": "hi",
        "score": 620,
        "customer_name": "Rajesh Kumar",
    }
    create_letter_pdf(data, output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000


def test_create_letter_pdf_english(tmp_path):
    output_path = os.path.join(tmp_path, "test_letter_en.pdf")
    data = {
        "letter": "GREETING: Dear John,\n\nINTRO: Your score is 780 — this is great!\n\nSCORE_PROJECTION:\nCurrent: 780\nAfter fixing all issues: 780-800\nTimeline: N/A\n\nCLOSING: Keep up the good work!\n\nDISPUTE_LETTERS:\nNone needed.",
        "language": "en",
        "score": 780,
        "customer_name": "John Doe",
    }
    create_letter_pdf(data, output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000


def test_create_letter_pdf_tamil(tmp_path):
    output_path = os.path.join(tmp_path, "test_letter_ta.pdf")
    data = {
        "letter": "GREETING: ராஜேஷ் அவர்களே,\n\nINTRO: உங்கள் ஸ்கோர் 780 — இது மிகவும் நல்லது!\n\nSCORE_PROJECTION:\nCurrent: 780\nAfter fixing all issues: 780-800\nTimeline: N/A\n\nCLOSING: தொடர்ந்து நல்ல பழக்கத்தை பின்பற்றுங்கள்!\n\nDISPUTE_LETTERS:\nNone needed.",
        "language": "ta",
        "score": 780,
        "customer_name": "ராஜேஷ் குமார்",
    }
    create_letter_pdf(data, output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000


def test_font_manager_recovers_from_corrupt_or_empty_font():
    from app.utils.font_manager import ensure_fonts, FONTS_DIR, _registered_fonts
    
    # We will target Gujarati font for this test as it's not yet registered in tests.
    lang = "gu"
    reg_font_name = "NotoSansGujarati"
    bold_font_name = "NotoSansGujarati-Bold"
    
    # Force the download path by making sure they are not registered in the local python run
    _registered_fonts.discard(reg_font_name)
    _registered_fonts.discard(bold_font_name)
    _registered_fonts.discard("NotoSansGujarati")
    
    reg_file_path = os.path.join(FONTS_DIR, "NotoSansGujarati-Regular.ttf")
    bold_file_path = os.path.join(FONTS_DIR, "NotoSansGujarati-Bold.ttf")
    
    # Ensure fonts dir exists
    os.makedirs(FONTS_DIR, exist_ok=True)
    
    # Delete if they already exist
    for path in [reg_file_path, bold_file_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
                
    # 1. Create a 0-byte file for Regular
    with open(reg_file_path, "wb") as f:
        f.write(b"")
        
    # 2. Create a corrupt/invalid header file for Bold (size > 1000 to pass size check but fail registration)
    with open(bold_file_path, "wb") as f:
        f.write(b"corrupt font data" * 100)
        
    # 3. Call ensure_fonts
    reg, bold = ensure_fonts("gu")
    
    # 4. Verify self-healing:
    # - The 0-byte file should be redownloaded.
    # - The corrupt bold file should fail registration, be deleted, redownloaded, and successfully registered.
    assert reg == reg_font_name
    assert bold == bold_font_name
    assert os.path.exists(reg_file_path)
    assert os.path.exists(bold_file_path)
    assert os.path.getsize(reg_file_path) > 1000
    assert os.path.getsize(bold_file_path) > 1000



