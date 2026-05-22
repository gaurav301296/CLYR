"""
CLYR API -- Secrets Management
Validates that all required secrets are present at startup.
Prevents running with missing or default credentials.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

REQUIRED_SECRETS = {
    "OPENAI_API_KEY": "OpenAI API key for LLM parsing",
    "SUPABASE_URL": "Supabase project URL",
    "SUPABASE_ANON_KEY": "Supabase anonymous key",
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key",
    "RAZORPAY_KEY_ID": "Razorpay API key ID",
    "RAZORPAY_KEY_SECRET": "Razorpay API secret",
}

OPTIONAL_SECRETS = {
    "SUPABASE_JWT_SECRET": "Supabase JWT secret for token verification",
    "CORS_ORIGINS": "Allowed CORS origins (defaults to localhost)",
    "RATE_LIMIT_RPM": "Rate limit per minute (defaults to 60)",
}


def validate_secrets(strict: bool = False):
    """
    Validate that all required secrets are present.
    In strict mode (production), exits if any are missing.
    In dev mode, logs warnings for missing secrets.
    """
    missing = []
    for key, description in REQUIRED_SECRETS.items():
        value = os.environ.get(key, "")
        if not value or value.startswith("your-") or value.startswith("sk-your"):
            missing.append((key, description))

    if missing:
        for key, description in missing:
            logger.warning(f"Missing or default secret: {key} ({description})")

        if strict:
            logger.error("Missing required secrets. Set them in .env or environment.")
            sys.exit(1)

    # Check for common security misconfigurations
    if os.environ.get("OPENAI_API_KEY", "").startswith("sk-test"):
        logger.warning("Using a test OpenAI API key. Real reports will not be analyzed.")

    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        if "localhost" in os.environ.get("CORS_ORIGINS", ""):
            logger.error("Production CORS contains localhost. This is a security risk.")
            sys.exit(1)

        if os.environ.get("RAZORPAY_KEY_ID", "").startswith("rzp_test"):
            logger.error("Production using Razorpay test keys. Real payments will not work.")
            sys.exit(1)

    return len(missing) == 0
