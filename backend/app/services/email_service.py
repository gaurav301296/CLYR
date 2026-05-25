"""
CLYR v2 — Email Service
Transactional emails via Resend API.
Sends: welcome, payment receipt, report-ready notification.
"""
import logging
from typing import Optional
from app.config import config

logger = logging.getLogger(__name__)

try:
    import resend
    _resend_available = True
except ImportError:
    _resend_available = False
    logger.warning("resend package not installed. Email sending disabled.")


def _get_client():
    """Get Resend client instance."""
    if not _resend_available or not config.resend_api_key:
        return None
    resend.api_key = config.resend_api_key
    return resend


def send_email(to: str, subject: str, html_content: str) -> bool:
    """
    Send a transactional email via Resend.
    
    Args:
        to: Recipient email address
        subject: Email subject
        html_content: HTML body content
    
    Returns:
        True if sent successfully, False otherwise
    """
    client = _get_client()
    if not client:
        logger.warning("Email not sent (no API key or resend not installed). To: %s, Subject: %s", to, subject)
        return False

    try:
        result = client.Emails.send({
            "from": config.email_from,
            "to": to,
            "subject": subject,
            "html": html_content,
        })
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_welcome_email(email: str, name: str = "") -> bool:
    """Send welcome email after signup."""
    display_name = name or "there"
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background: #0F172A; color: #F8FAFC;">
        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #F59E0B, #FBBF24); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CLYR</h1>
        </div>
        <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 16px;">Welcome, {display_name}!</h2>
        <p style="font-size: 16px; color: #CBD5E1; line-height: 1.6; margin-bottom: 24px;">
            Thanks for joining CLYR. You're now ready to take control of your credit score.
        </p>
        <div style="background: #1A2332; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
            <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">Quick Start:</h3>
            <ol style="color: #CBD5E1; padding-left: 20px; line-height: 1.8;">
                <li>Upload your CIBIL/credit report PDF</li>
                <li>Get your personalized analysis in 30 seconds</li>
                <li>Download your recovery roadmap + dispute letters</li>
            </ol>
        </div>
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="https://clyr.in" style="display: inline-block; background: #F59E0B; color: #0F172A; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">Upload Your Report →</a>
        </div>
        <p style="font-size: 13px; color: #94A3B8; text-align: center; margin-top: 32px;">
            Questions? Just reply to this email.<br>
            © {__import__('datetime').datetime.now().year} CLYR. All rights reserved.
        </p>
    </div>
    """
    return send_email(email, "Welcome to CLYR — Let's Fix Your Credit Score", html)


def send_payment_receipt(email: str, name: str, plan: str, amount_inr: int, report_id: str = "") -> bool:
    """Send payment receipt after successful purchase."""
    display_name = name or "there"
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background: #0F172A; color: #F8FAFC;">
        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="font-size: 28px; font-weight: 800; color: #F59E0B;">CLYR</h1>
        </div>
        <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 16px;">Payment Confirmed ✓</h2>
        <p style="font-size: 16px; color: #CBD5E1; line-height: 1.6; margin-bottom: 24px;">
            Hey {display_name}, your payment has been received. Here's your receipt:
        </p>
        <div style="background: #1A2332; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #94A3B8; font-size: 14px;">Plan</td>
                    <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 14px;">{plan}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #94A3B8; font-size: 14px;">Amount</td>
                    <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 14px;">₹{amount_inr}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #94A3B8; font-size: 14px;">Status</td>
                    <td style="padding: 8px 0; text-align: right; color: #10B981; font-weight: 600; font-size: 14px;">Paid ✓</td>
                </tr>
                {f'<tr><td style="padding: 8px 0; color: #94A3B8; font-size: 14px;">Report ID</td><td style="padding: 8px 0; text-align: right; font-size: 12px; color: #94A3B8;">{report_id[:12]}...</td></tr>' if report_id else ''}
            </table>
        </div>
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="https://clyr.in/upload" style="display: inline-block; background: #F59E0B; color: #0F172A; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">Upload Your Report →</a>
        </div>
        <p style="font-size: 13px; color: #94A3B8; text-align: center; margin-top: 32px;">
            Questions? Reply to this email.<br>
            © {__import__('datetime').datetime.now().year} CLYR. All rights reserved.
        </p>
    </div>
    """
    return send_email(email, f"CLYR Payment Receipt — {plan} Plan", html)


def send_report_ready_email(email: str, name: str, score: int, issues_count: int, report_url: str = "") -> bool:
    """Send notification when report analysis is complete."""
    display_name = name or "there"
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background: #0F172A; color: #F8FAFC;">
        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="font-size: 28px; font-weight: 800; color: #F59E0B;">CLYR</h1>
        </div>
        <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 16px;">Your Report is Ready! 🎉</h2>
        <p style="font-size: 16px; color: #CBD5E1; line-height: 1.6; margin-bottom: 24px;">
            Hey {display_name}, we've analyzed your credit report. Here's what we found:
        </p>
        <div style="background: #1A2332; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; text-align: center;">
            <div style="font-size: 48px; font-weight: 800; {('color: #10B981;' if score >= 700 else 'color: #F59E0b;' if score >= 650 else 'color: #EF4444;')}">{score}</div>
            <div style="font-size: 14px; color: #94A3B8; margin-top: 8px;">Credit Score</div>
            <div style="font-size: 14px; color: #CBD5E1; margin-top: 16px;">
                {issues_count} issue{'s' if issues_count != 1 else ''} found that we can help you fix.
            </div>
        </div>
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="{report_url or 'https://clyr.in/dashboard'}" style="display: inline-block; background: #F59E0B; color: #0F172A; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 16px;">View Your Analysis →</a>
        </div>
        <p style="font-size: 13px; color: #94A3B8; text-align: center; margin-top: 32px;">
            © {__import__('datetime').datetime.now().year} CLYR. All rights reserved.
        </p>
    </div>
    """
    return send_email(email, f"Your CLYR Report is Ready — Score: {score}", html)
