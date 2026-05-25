"""
CLYR v2 — Main Application (Hybrid: SQLite + JWT auth)
FastAPI app with all middleware, routes, and startup validation.
Keeps v2 design system, uses v1 local SQLite + JWT for data layer.
"""
import logging
import sys

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import config
from app.database import init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Validate Config ──────────────────────────────────────────────────────────
config_errors = config.validate()
if config_errors:
    for error in config_errors:
        logger.warning("Config: %s", error)
    if config.environment == "production":
        logger.error("FATAL: Missing required config in production")
        sys.exit(1)

# ── Create App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="CLYR API",
    version="2.0.0",
    description="AI-powered credit report analysis and recovery roadmap generator",
    docs_url="/api/docs" if config.debug else None,
    redoc_url="/api/redoc" if config.debug else None,
)

# ── Middleware (order matters: first added = outermost) ──────────────────────

# 1. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=config.rate_limit_rpm,
    upload_limit=config.rate_limit_upload_rpm,
)

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sentry ───────────────────────────────────────────────────────────────────
if config.sentry_dsn:
    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.environment,
        integrations=[FastApiIntegration(), sentry_logging],
        traces_sample_rate=0.1,
    )
    logger.info("Sentry initialized")

# ── Import and Register Routes ───────────────────────────────────────────────
from app.routes.health import router as health_router
from app.routes.reports import router as reports_router
from app.routes.waitlist import router as waitlist_router
from app.routes.admin import router as admin_router
from app.routes.user_routes import router as user_router
from app.routes.payments import router as payments_router

app.include_router(health_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(waitlist_router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(user_router)  # already has /api prefix
app.include_router(payments_router, prefix="/api/payments")

# ── Serve Frontend (production) ─────────────────────────────────────────────
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Serve React SPA for all non-API routes."""
        return HTMLResponse(Path(frontend_dist / "index.html").read_text())


# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    logger.info("CLYR v2 API started — SQLite + JWT auth (hybrid mode)")


from fastapi.responses import HTMLResponse
