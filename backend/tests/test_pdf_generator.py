import os
import pytest
from app.utils.pdf_generator import create_report_pdf

def test_create_report_pdf_file_creation(tmp_path):
    output_path = os.path.join(tmp_path, "test_report.pdf")
    data = {
        "score": 620,
        "customer_name": "Rajesh Kumar",
        "general_health": "Needs Attention",
        "issues": [
            {"account": "HDFC Card", "type": "Red", "details": "Written off ₹45,000", "action": "Contact bank", "impact": "High"}
        ],
        "action_steps": ["Step 1", "Step 2"],
        "timeline": [
            {"phase": "Month 1", "task": "Resolve HDFC Settlement", "status": "Critical"}
        ]
    }
    create_report_pdf(data, output_path)
    assert os.path.exists(output_path)

def test_create_report_pdf_hindi(tmp_path):
    output_path = os.path.join(tmp_path, "test_report_hi.pdf")
    data = {
        "score": 780,
        "customer_name": "राजेश कुमार",
        "general_health": "उत्कृष्ट",
        "issues": [],
        "action_steps": ["समय पर भुगतान करें"],
        "timeline": []
    }
    create_report_pdf(data, output_path, language="hi")
    assert os.path.exists(output_path)

def test_create_report_pdf_tamil(tmp_path):
    output_path = os.path.join(tmp_path, "test_report_ta.pdf")
    data = {
        "score": 780,
        "customer_name": "ராஜேஷ் குமார்",
        "general_health": "சிறந்தது",
        "issues": [],
        "action_steps": ["நெறிமுறைகளைப் பின்பற்றவும்"],
        "timeline": []
    }
    create_report_pdf(data, output_path, language="ta")
    assert os.path.exists(output_path)

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



