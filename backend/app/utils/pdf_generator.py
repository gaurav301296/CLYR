import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.utils.font_manager import get_font_names
from app.i18n.translations import PDF_LABELS
from app.utils.sanitization import sanitize_pdf_text

def create_report_pdf(data: dict, output_path: str, language: str = "en"):
    """
    Generates a premium, high-fidelity PDF credit summary and recovery roadmap.
    """
    # Normalize language code
    language = language.lower().strip() if language else "en"
    if language not in PDF_LABELS:
        language = "en"

    # Get resolved fonts for the current language
    reg_font, bold_font = get_font_names(language)

    # Create the document with A4 size and 0.5 inch (36 points) margins for clean space utilization
    margin = 36
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    # Base width calculations
    # A4 width = 595.27. Printable width = 595.27 - 72 = 523.27
    printable_width = 523.27
    
    styles = getSampleStyleSheet()
    
    # Custom Premium Color Palette
    primary_color = colors.HexColor("#0F172A")    # Deep Slate / Dark Navy
    secondary_color = colors.HexColor("#475569")  # Slate Gray
    accent_blue = colors.HexColor("#2563EB")      # Premium Royal Blue
    background_light = colors.HexColor("#F8FAFC") # Soft Off-White
    border_color = colors.HexColor("#E2E8F0")     # Light Slate border
    
    color_red = colors.HexColor("#DC2626")        # Rich Red
    color_yellow = colors.HexColor("#D97706")     # Warm Amber/Yellow
    color_green = colors.HexColor("#16A34A")      # Safe Green
    
    bg_red = colors.HexColor("#FEF2F2")
    bg_yellow = colors.HexColor("#FEF3C7")
    bg_green = colors.HexColor("#ECFDF5")
    
    # Custom Typography Styles using dynamically resolved fonts
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=4
    )
    
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    style_h1 = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=10,
        leading=14,
        textColor=primary_color
    )
    
    style_body_bold = ParagraphStyle(
        'BodyTextBoldCustom',
        parent=style_body,
        fontName=bold_font
    )
    
    style_body_muted = ParagraphStyle(
        'BodyTextMutedCustom',
        parent=style_body,
        fontName=reg_font,
        fontSize=9,
        leading=13,
        textColor=secondary_color
    )
    
    style_bullet = ParagraphStyle(
        'BulletCustom',
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # --- HEADER SECTION ---
    header_data = [
        [
            Paragraph(PDF_LABELS[language]['brand'], style_title),
            Paragraph(f"<b>{PDF_LABELS[language]['client_report']}</b><br/>{PDF_LABELS[language]['confidential']}", ParagraphStyle('RightHeader', parent=style_body, alignment=TA_RIGHT, fontSize=9, textColor=secondary_color))
        ]
    ]
    header_table = Table(header_data, colWidths=[printable_width * 0.6, printable_width * 0.4])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Paragraph(PDF_LABELS[language]['subtitle'], style_subtitle))
    
    # Decorative colored accent line
    divider = Table([[""]], colWidths=[printable_width], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), accent_blue),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))
    
    # --- CLIENT & SCORE OVERVIEW BLOCK ---
    score = data.get("score", 300)
    customer_name = sanitize_pdf_text(data.get("customer_name", "Valued Customer"))
    general_health = sanitize_pdf_text(data.get("general_health", "N/A"))
    
    # Decide score colors
    if score >= 750:
        score_color = color_green
        score_bg = bg_green
    elif score >= 700:
        score_color = colors.HexColor("#2563EB")
        score_bg = colors.HexColor("#EFF6FF")
    elif score >= 620:
        score_color = color_yellow
        score_bg = bg_yellow
    else:
        score_color = color_red
        score_bg = bg_red
        
    score_p = Paragraph(f"<font size=10 color='#475569'>{PDF_LABELS[language]['current_score']}</font><br/><font size=36 color='{score_color.hexval()}'><b>{score}</b></font><br/><font size=11 color='{score_color.hexval()}'><b>{general_health}</b></font>", ParagraphStyle('ScorePara', parent=style_body, alignment=TA_CENTER, leading=20))
    client_info_text = (
        f"<b>{PDF_LABELS[language]['client_name']}:</b> {customer_name}<br/>"
        f"<b>{PDF_LABELS[language]['analysis_date']}:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>"
        f"<b>{PDF_LABELS[language]['report_id']}:</b> CS-{score}-{abs(hash(customer_name)) % 10000:04d}<br/>"
        f"<b>{PDF_LABELS[language]['scope']}:</b> {PDF_LABELS[language]['scope_desc']}"
    )
    client_info_p = Paragraph(client_info_text, ParagraphStyle('ClientInfoPara', parent=style_body, leading=16))
    
    overview_table_data = [
        [score_p, client_info_p]
    ]
    overview_table = Table(overview_table_data, colWidths=[printable_width * 0.4, printable_width * 0.6])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), score_bg),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 1, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 15))
    
    # --- CRITICAL ISSUES ("WHAT IS BROKEN") ---
    issues = data.get("issues", [])
    if issues:
        story.append(Paragraph(PDF_LABELS[language]['critical_issues'], style_h1))
        
        for issue in issues:
            issue_type = issue.get("type", "Yellow")
            account_name = sanitize_pdf_text(issue.get("account", "Account"))
            details = sanitize_pdf_text(issue.get("details", ""))
            action = sanitize_pdf_text(issue.get("action", ""))
            
            # Determine color-coding
            if issue_type.upper() == "RED":
                bar_color = color_red
                badge_text = f"<font color='{color_red.hexval()}'><b>{PDF_LABELS[language]['critical_badge']}</b></font>"
            else:
                bar_color = color_yellow
                badge_text = f"<font color='{color_yellow.hexval()}'><b>{PDF_LABELS[language]['attention_badge']}</b></font>"
                
            issue_title_p = Paragraph(f"<b>{account_name}</b>: {badge_text}", style_body_bold)
            issue_details_p = Paragraph(f"<b>{PDF_LABELS[language]['what_broken']}:</b> {details}", style_body)
            issue_action_p = Paragraph(f"<b>{PDF_LABELS[language]['how_resolve']}:</b> {action}", style_body)
            
            # A 2-column table: thin left border bar, and content block
            content_cell = [
                issue_title_p,
                Spacer(1, 4),
                issue_details_p,
                Spacer(1, 4),
                issue_action_p
            ]
            
            issue_table_data = [
                ["", content_cell]
            ]
            
            issue_table = Table(issue_table_data, colWidths=[4, printable_width - 6])
            issue_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0), bar_color),
                ('BACKGROUND', (1,0), (1,0), background_light),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (1,0), (1,0), 12),
                ('RIGHTPADDING', (1,0), (1,0), 12),
                ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ]))
            story.append(issue_table)
            story.append(Spacer(1, 8))
            
        story.append(Spacer(1, 10))
    else:
        # Green profile text
        story.append(Paragraph(PDF_LABELS[language]['no_issues'], style_h1))
        no_issue_p = Paragraph(PDF_LABELS[language]['no_issues_desc'], style_body)
        story.append(no_issue_p)
        story.append(Spacer(1, 15))
 
    # --- STEP-BY-STEP REPAIR CHECKLIST ("HOW TO FIX IT") ---
    action_steps = data.get("action_steps", [])
    if action_steps:
        checklist_elements = []
        checklist_elements.append(Paragraph(PDF_LABELS[language]['checklist_title'], style_h1))
        
        for step in action_steps:
            bullet_p = Paragraph(f"&bull;&nbsp;&nbsp; {step}", style_bullet)
            checklist_elements.append(bullet_p)
            
        story.append(KeepTogether(checklist_elements))
        story.append(Spacer(1, 15))
        
    # --- TIMELINE & EXPECTED RECOVERY ("HOW LONG IT TAKES") ---
    timeline = data.get("timeline", [])
    if timeline:
        timeline_elements = []
        timeline_elements.append(Paragraph(PDF_LABELS[language]['timeline_title'], style_h1))
        
        # Build table header
        table_content = [[
            Paragraph(f"<b>{PDF_LABELS[language]['col_timeline']}</b>", style_body_bold),
            Paragraph(f"<b>{PDF_LABELS[language]['col_task']}</b>", style_body_bold),
            Paragraph(f"<b>{PDF_LABELS[language]['col_priority']}</b>", style_body_bold)
        ]]
        
        for item in timeline:
            phase = item.get("phase", "Phase")
            task = item.get("task", "")
            status = item.get("status", "")
            
            # Highlight status text
            if status.upper() in ["CRITICAL", "HIGH"]:
                status_formatted = f"<font color='{color_red.hexval()}'><b>{status}</b></font>"
            elif status.upper() in ["IN PROGRESS", "MEDIUM"]:
                status_formatted = f"<font color='{color_yellow.hexval()}'><b>{status}</b></font>"
            else:
                status_formatted = f"<font color='{color_green.hexval()}'><b>{status}</b></font>"
                
            table_content.append([
                Paragraph(phase, style_body_bold),
                Paragraph(task, style_body),
                Paragraph(status_formatted, style_body)
            ])
            
        timeline_table = Table(table_content, colWidths=[printable_width * 0.2, printable_width * 0.6, printable_width * 0.2])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), background_light),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, background_light]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        timeline_elements.append(timeline_table)
        timeline_elements.append(Spacer(1, 10))
        
        # Disclaimer / Notes
        disclaimer_text = PDF_LABELS[language]['disclaimer']
        timeline_elements.append(Paragraph(disclaimer_text, style_body_muted))
        
        story.append(KeepTogether(timeline_elements))
        
    # Build the document
    doc.build(story)
