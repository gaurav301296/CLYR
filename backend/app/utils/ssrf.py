"""
CLYR API -- SSRF Prevention
Validates URLs before making outbound requests.
"""
import re
from urllib.parse import urlparse


BLOCKED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",  # AWS metadata
]

BLOCKED_SCHEMES = ["file", "ftp", "gopher", "dict"]


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe to request.
    Prevents SSRF attacks by blocking internal IPs and dangerous schemes.
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme in BLOCKED_SCHEMES:
            return False

        # Check for IP-based SSRF
        hostname = parsed.hostname or ""
        if hostname in BLOCKED_HOSTS:
            return False

        # Check for private IP ranges
        if re.match(r'^10\.', hostname):
            return False
        if re.match(r'^172\.(1[6-9]|2[0-9]|3[01])\.', hostname):
            return False
        if re.match(r'^192\.168\.', hostname):
            return False
        if re.match(r'^127\.', hostname):
            return False

        return True
    except Exception:
        return False
