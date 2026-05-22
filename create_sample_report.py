from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sample():
    pdf_path = "sample_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28
    )
    story.append(Paragraph("CONFIDENTIAL CIBIL TRANSUNION CREDIT REPORT", title_style))
    story.append(Spacer(1, 20))
    
    # Body text with standard patterns
    normal_style = styles['Normal']
    
    content = [
        "<b>REPORT INFORMATION</b>",
        "REPORT DATE: 2026-05-20",
        "<b>CONSUMER PROFILE</b>",
        "CONSUMER NAME: Rajesh Kumar",
        "PAN NUMBER: ABCDE1234F",
        "<b>CREDIT RATING SUMMARY</b>",
        "CIBIL TRANSUNION SCORE: 590",
        "RATING STATUS: POOR / NEEDS ATTENTION",
        "<b>ACCOUNT DETAILS & HISTORY</b>",
        "ACCOUNT 1: HDFC BANK CREDIT CARD",
        "ACCOUNT TYPE: REVOLVING CREDIT",
        "SANCTIONED AMOUNT: 100,000 INR",
        "CURRENT BALANCE: 85,000 INR",
        "PAYMENT STATUS: OVERDUE DPD 60 DAYS",
        "REMARKS: SETTLED WITH LOSS",
        "ACCOUNT 2: SBI PERSONAL LOAN",
        "ACCOUNT TYPE: TERM LOAN",
        "SANCTIONED AMOUNT: 250,000 INR",
        "PAYMENT STATUS: LATE PAYMENT DPD 90 DAYS",
        "REMARKS: WRITTEN OFF",
        "ACCOUNT 3: ICICI HOME LOAN",
        "ACCOUNT TYPE: SECURED LOAN",
        "PAYMENT STATUS: ACTIVE / NO DELAY",
        "REMARKS: CLEAN PAYMENT RECORD"
    ]
    
    for text in content:
        story.append(Paragraph(text, normal_style))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    print(f"Sample PDF successfully generated at: {pdf_path}")

if __name__ == "__main__":
    generate_sample()
