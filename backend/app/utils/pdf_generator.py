"""
CLYR PDF Generator — Produces a personalized vernacular credit analysis letter.

Output: A PDF that looks like a personal letter from a smart friend who works in banking.
Not a formal report. Not a dashboard. A letter.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from app.utils.font_manager import get_font_names
from app.utils.sanitization import sanitize_pdf_text


def create_letter_pdf(letter_data: dict, output_path: str):
    """
    Generate a personalized credit analysis letter as a PDF.
    
    letter_data should contain:
    - letter: The full letter text (from LLM or regex fallback)
    - language: Language code (en, hi, bn, te, mr, ta, gu, kn, ml, pa)
    - score: Credit score
    - customer_name: Customer name
    """
    language = letter_data.get("language", "en").lower().strip()
    letter_text = letter_data.get("letter", "")
    score = letter_data.get("score", 0)
    customer_name = letter_data.get("customer_name", "Customer")

    # Get fonts for the language
    reg_font, bold_font = get_font_names(language)

    margin = 40
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    printable_width = 595.27 - (2 * margin)

    # Color palette — warm, friendly, not corporate
    text_dark = colors.HexColor("#1a1a2e")      # Near-black for body
    text_mid = colors.HexColor("#4a4a68")        # Gray for secondary
    accent_warm = colors.HexColor("#e85d04")     # Warm orange for highlights
    accent_blue = colors.HexColor("#2563eb")     # Blue for links/actions
    bg_warm = colors.HexColor("#fff8f0")         # Warm cream for boxes
    bg_blue = colors.HexColor("#eff6ff")         # Light blue for info boxes
    border_color = colors.HexColor("#e0d6cc")    # Warm border

    styles = getSampleStyleSheet()

    # Letter-style heading (like a personal letter)
    style_heading = ParagraphStyle(
        'LetterHeading',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=18,
        leading=24,
        textColor=text_dark,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    style_subheading = ParagraphStyle(
        'LetterSubheading',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=10,
        leading=14,
        textColor=text_mid,
        spaceAfter=20,
        alignment=TA_LEFT,
    )

    style_body = ParagraphStyle(
        'LetterBody',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=11,
        leading=17,
        textColor=text_dark,
        spaceAfter=10,
        alignment=TA_LEFT,
    )

    style_bold = ParagraphStyle(
        'LetterBold',
        parent=style_body,
        fontName=bold_font,
    )

    style_issue_title = ParagraphStyle(
        'IssueTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=13,
        leading=18,
        textColor=accent_warm,
        spaceBefore=16,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    style_action = ParagraphStyle(
        'ActionStep',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=10,
        leading=15,
        textColor=text_dark,
        leftIndent=20,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    style_box_label = ParagraphStyle(
        'BoxLabel',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=9,
        leading=12,
        textColor=text_mid,
        alignment=TA_LEFT,
    )

    style_box_value = ParagraphStyle(
        'BoxValue',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=14,
        leading=18,
        textColor=text_dark,
        alignment=TA_LEFT,
    )

    style_disclaimer = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=8,
        leading=12,
        textColor=text_mid,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    style_closing = ParagraphStyle(
        'Closing',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=11,
        leading=17,
        textColor=text_dark,
        spaceBefore=16,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────
    # CLYR branding — small, clean, not corporate
    header_data = [
        [
            Paragraph("CLYR", ParagraphStyle('Brand', parent=styles['Normal'], fontName=bold_font, fontSize=16, textColor=accent_warm)),
            Paragraph(
                f"Credit Analysis — {datetime.now().strftime('%B %Y')}",
                ParagraphStyle('Date', parent=styles['Normal'], fontName=reg_font, fontSize=9, textColor=text_mid, alignment=TA_LEFT)
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[printable_width * 0.5, printable_width * 0.5])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=20))

    # ── PARSE AND RENDER LETTER ──────────────────────────────────────────
    # The letter comes from the LLM as structured text. We parse sections
    # and render them with appropriate formatting.

    lines = letter_text.split('\n')
    in_dispute_letters = False
    current_section = None
    dispute_letter_buffer = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Section headers
        if line.startswith("GREETING:"):
            greeting = line.split("GREETING:", 1)[1].strip()
            story.append(Paragraph(greeting, style_heading))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if line.startswith("INTRO:"):
            intro = line.split("INTRO:", 1)[1].strip()
            story.append(Paragraph(intro, style_body))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if line.startswith("ISSUE #"):
            # Issue title
            story.append(Paragraph(line, style_issue_title))
            i += 1
            continue

        if line.startswith("WHAT:"):
            what = line.split("WHAT:", 1)[1].strip()
            story.append(Paragraph(f"<b>Problem:</b> {sanitize_pdf_text(what)}", style_body))
            i += 1
            continue

        if line.startswith("IMPACT:"):
            impact = line.split("IMPACT:", 1)[1].strip()
            story.append(Paragraph(f"<b>Score Impact:</b> {sanitize_pdf_text(impact)}", style_body))
            i += 1
            continue

        if line.startswith("ACTION:"):
            action = line.split("ACTION:", 1)[1].strip()
            story.append(Paragraph(f"<b>What to do:</b>", style_bold))
            # Action might be multi-line
            action_lines = [action]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("TIMELINE:", "SUCCESS_CHANCE:", "ISSUE #", "SCORE_PROJECTION:", "CLOSING:", "DISPUTE_LETTERS:")):
                action_lines.append(lines[j].strip())
                j += 1
            for al in action_lines:
                story.append(Paragraph(f"• {sanitize_pdf_text(al)}", style_action))
            i = j
            continue

        if line.startswith("TIMELINE:"):
            timeline = line.split("TIMELINE:", 1)[1].strip()
            story.append(Paragraph(f"<b>Timeline:</b> {sanitize_pdf_text(timeline)}", style_body))
            i += 1
            continue

        if line.startswith("SUCCESS_CHANCE:"):
            chance = line.split("SUCCESS_CHANCE:", 1)[1].strip()
            story.append(Paragraph(f"<b>Success chance:</b> {sanitize_pdf_text(chance)}", style_body))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if line.startswith("SCORE_PROJECTION:"):
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=12))
            story.append(Paragraph("<b>Score Projection</b>", style_bold))

            # Build projection table
            proj_data = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                pline = lines[j].strip()
                if pline.startswith("Current:"):
                    val = pline.split(":", 1)[1].strip()
                    proj_data.append(["Current Score", val])
                elif pline.startswith("After fixing"):
                    val = pline.split(":", 1)[1].strip()
                    proj_data.append(["After All Fixes", val])
                elif pline.startswith("Timeline:"):
                    val = pline.split(":", 1)[1].strip()
                    proj_data.append(["Expected Timeline", val])
                elif pline.startswith(("CLOSING:", "DISPUTE_LETTERS:")):
                    break
                j += 1

            if proj_data:
                proj_table = Table(proj_data, colWidths=[printable_width * 0.4, printable_width * 0.6])
                proj_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), bg_warm),
                    ('BACKGROUND', (1, 0), (1, -1), bg_blue),
                    ('FONTNAME', (0, 0), (-1, -1), reg_font),
                    ('FONTNAME', (0, 0), (0, -1), bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (-1, -1), text_dark),
                    ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                story.append(proj_table)

            i = j
            continue

        if line.startswith("CLOSING:"):
            closing = line.split("CLOSING:", 1)[1].strip()
            story.append(Spacer(1, 16))
            story.append(Paragraph(sanitize_pdf_text(closing), style_closing))
            i += 1
            continue

        if line.startswith("DISPUTE_LETTERS:"):
            in_dispute_letters = True
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="100%", thickness=1, color=accent_warm, spaceAfter=12))
            story.append(Paragraph("<b>📝 Ready-to-Send Dispute Letters</b>", style_issue_title))
            story.append(Paragraph(
                "Copy these letters and send them to the respective banks or CIBIL. "
                "You can send them by email, post, or submit online through the bank's dispute portal.",
                style_disclaimer
            ))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if in_dispute_letters:
            # Collect dispute letter content
            if line.startswith("---") or line.startswith("Letter #") or line.startswith("To:"):
                dispute_letter_buffer.append(line)
            elif line.startswith("Subject:") or line.startswith("Dear") or line.startswith("Respected"):
                dispute_letter_buffer.append(line)
            elif line:
                dispute_letter_buffer.append(line)

            # Render accumulated letter on separator
            if line.startswith("---") and dispute_letter_buffer:
                letter_content = "<br/>".join([sanitize_pdf_text(l) for l in dispute_letter_buffer if l.strip() and not l.strip().startswith("---")])
                if letter_content.strip():
                    story.append(Spacer(1, 12))
                    # Letter box
                    letter_para = Paragraph(letter_content, ParagraphStyle(
                        'DisputeLetter',
                        parent=styles['Normal'],
                        fontName=reg_font,
                        fontSize=9,
                        leading=13,
                        textColor=text_dark,
                        leftIndent=16,
                        rightIndent=16,
                        spaceAfter=8,
                    ))
                    story.append(letter_para)
                    story.append(HRFlowable(width="80%", thickness=0.5, color=border_color, spaceAfter=8, spaceBefore=4))
                dispute_letter_buffer = []
            i += 1
            continue

        # Default: render as body text
        story.append(Paragraph(sanitize_pdf_text(line), style_body))
        i += 1

    # ── FOOTER ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=8))
    story.append(Paragraph(
        "⚠️ Disclaimer: This analysis is generated from your credit report using AI. "
        "It is for informational purposes only and does not constitute legal or financial advice. "
        "Always verify with your bank or a qualified professional before taking action.",
        style_disclaimer
    ))
    story.append(Paragraph(
        f"Generated by CLYR • {datetime.now().strftime('%d %B %Y')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontName=reg_font, fontSize=7, textColor=text_mid)
    ))

    doc.build(story)
