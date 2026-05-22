"""
CLYR API -- Security Event Logging
Logs all security-relevant events for audit trail.
"""
import logging
import json
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("security")


def log_security_event(
    event_type: str,
    details: str,
    client_ip: Optional[str] = None,
    user_id: Optional[str] = None,
    severity: str = "INFO",
):
    """Log a security event with structured data."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
        "client_ip": client_ip,
        "user_id": user_id,
        "severity": severity,
    }
    log_func = getattr(logger, severity.lower(), logger.info)
    log_func(json.dumps(event))


def log_auth_event(user_id: str, action: str, success: bool, client_ip: str = None):
    """Log authentication events."""
    log_security_event(
        event_type=f"auth_{action}",
        details=f"Authentication {action}: {'success' if success else 'failed'}",
        client_ip=client_ip,
        user_id=user_id,
        severity="INFO" if success else "WARNING",
    )


def log_access_event(user_id: str, resource: str, action: str, allowed: bool, client_ip: str = None):
    """Log access control events."""
    log_security_event(
        event_type="access_control",
        detail=f"{action} on {resource}: {'allowed' if allowed else 'denied'}",
        client_ip=client_ip,
        user_id=user_id,
        severity="INFO" if allowed else "WARNING",
    )


def log_payment_event(user_id: str, order_id: str, action: str, success: bool, amount: int = 0):
    """Log payment events."""
    log_security_event(
        event_type=f"payment_{action}",
        details=f"Payment {action}: order={order_id}, amount={amount}, success={success}",
        user_id=user_id,
        severity="INFO" if success else "ERROR",
    )


def log_data_event(user_id: str, action: str, data_type: str, record_id: str = None):
    """Log data access events (GDPR/DPDP relevant)."""
    log_security_event(
        event_type=f"data_{action}",
        details=f"Data {action}: type={data_type}, record={record_id}",
        user_ip=user_id,
        user_id=user_id,
    )
