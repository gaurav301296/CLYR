"""
CLYR v2 — Configuration Management
All environment variables validated at startup. No silent failures.
"""
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    # Server
    host: str = "0.0.0.0"
    port: int = 8005
    environment: str = "development"
    debug: bool = False

    # OpenRouter (LLM)
    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "openrouter/owl-alpha"

    # JWT
    jwt_secret: str = ""

    # Supabase (optional — SQLite used if not configured)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    # Rate Limiting
    rate_limit_rpm: int = 60
    rate_limit_upload_rpm: int = 10

    # CORS
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:80",
    ])

    # Email (for transactional emails)
    resend_api_key: str = ""
    email_from: str = "CLYR <hello@clyr.in>"

    # Sentry
    sentry_dsn: str = ""

    # Upload
    max_upload_size_mb: int = 10

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables with validation."""
        config = cls()

        # Server
        config.host = os.getenv("HOST", config.host)
        config.port = int(os.getenv("PORT", config.port))
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        config.debug = os.getenv("DEBUG", "false").lower() == "true"

        # OpenRouter
        config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        config.openai_base_url = os.getenv("OPENAI_BASE_URL", config.openai_base_url)
        config.openai_model = os.getenv("OPENAI_MODEL", config.openai_model)

        # JWT
        config.jwt_secret = os.getenv("JWT_SECRET", "")

        # Supabase (optional)
        config.supabase_url = os.getenv("SUPABASE_URL", "")
        config.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        config.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        config.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")

        # Razorpay
        config.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
        config.razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

        # Rate Limiting
        config.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", config.rate_limit_rpm))
        config.rate_limit_upload_rpm = int(os.getenv("RATE_LIMIT_UPLOAD_RPM", config.rate_limit_upload_rpm))

        # CORS
        cors = os.getenv("CORS_ORIGINS", "")
        if cors:
            config.cors_origins = [o.strip() for o in cors.split(",")]

        # Email
        config.resend_api_key = os.getenv("RESEND_API_KEY", "")
        config.email_from = os.getenv("EMAIL_FROM", config.email_from)

        # Sentry
        config.sentry_dsn = os.getenv("SENTRY_DSN", "")

        # Upload
        config.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", config.max_upload_size_mb))

        return config

    def validate(self) -> list[str]:
        """Validate that all required config is present. Returns list of errors."""
        errors = []

        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")

        # Production-specific checks
        if self.environment == "production":
            if not self.jwt_secret:
                errors.append("JWT_SECRET is required in production")
            if self.razorpay_key_id.startswith("rzp_test"):
                errors.append("Production should use Razorpay LIVE keys, not test keys")
            if "localhost" in ",".join(self.cors_origins):
                errors.append("CORS_ORIGINS should not contain localhost in production")
            if not self.sentry_dsn:
                errors.append("SENTRY_DSN is required in production")

        return errors


# Global config instance
config = Config.from_env()
