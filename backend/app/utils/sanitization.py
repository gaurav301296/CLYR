"""
CLYR API -- Input Sanitization Utilities
Prevents injection attacks in user-generated content rendered in PDFs.
"""
import re
import html


def sanitize_pdf_text(text: str) -> str:
    """
    Sanitize text before rendering in ReportLab PDF.
    Prevents HTML/script injection through crafted PDF content.
    """
    if not text:
        return ""
    # Escape HTML entities first
    text = html.escape(text)
    # Remove any remaining script-like patterns
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    # Limit length to prevent PDF generation abuse
    return text[:5000]


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename."""
    if not filename:
        return "report.pdf"
    # Remove path traversal attempts
    filename = re.sub(r'[\\/]', '', filename)
    # Remove null bytes
    filename = filename.replace('\x00', '')
    # Keep only safe characters
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # Ensure .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    return filename[:255]
