import os
import tempfile
import logging
from datetime import datetime
from fastapi.responses import HTMLResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.utils.parser import extract_pdf_text
from app.services.llm_service import generate_credit_summary
from app.utils.pdf_generator import create_letter_pdf
from app.utils.logging_config import logger
from app.routes.user_routes import router as user_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services import db_service

# MIME type check for PDF magic bytes
PDF_MAGIC = b"%PDF"

app = FastAPI(
    title="CLYR API",
    version="1.0.0",
    description="AI-powered credit report analysis and recovery roadmap generator",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Middleware stack (order matters -- first added = outermost)
# 1. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting
rpm = int(os.environ.get("RATE_LIMIT_RPM", "60"))
upload_rpm = int(os.environ.get("RATE_LIMIT_UPLOAD_RPM", "10"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=rpm, upload_limit=upload_rpm)

# 3. CORS
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:5174,http://localhost:5175,*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user routes
app.include_router(user_router)

# Initialize database
db_service.init_db()

logger.info("CLYR API initialized", extra={"version": "1.0.0"})

# Initialize Sentry error monitoring
sentry_dsn = os.environ.get("SENTRY_DSN", "")
if sentry_dsn:
    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "development"),
        integrations=[FastApiIntegration(), sentry_logging],
        traces_sample_rate=0.1,
    )
    logger.info("Sentry error monitoring initialized")

def remove_temp_file(path: str):
    """Background task to remove a temporary file after response transmission."""
    try:
        if os.path.exists(path):
            # Overwrite with zeros before deletion to reduce data remnant risk
            try:
                with open(path, "wb") as f:
                    f.write(b"\x00" * min(os.path.getsize(path), 4096))
            except OSError:
                pass
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), lang: str = "en"):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
            if len(content) < 100:
                raise HTTPException(status_code=400, detail="File is empty or too small to be a valid PDF.")
            if not content[:4].startswith(PDF_MAGIC):
                raise HTTPException(status_code=400, detail="File is not a valid PDF.")
            tmp.write(content)
            tmp_path = tmp.name
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    try:
        raw_text = extract_pdf_text(tmp_path)
        # Generate personalized letter in customer's language
        summary = generate_credit_summary(raw_text, language=lang)

        # Determine health summary
        score = summary.get("score", 0)
        if score >= 750:
            health = "Excellent"
        elif score >= 700:
            health = "Good"
        elif score >= 650:
            health = "Fair"
        else:
            health = "Needs Attention"

        # Save report to database (anonymous or authenticated)
        try:
            # Try to get user from optional auth header
            from app.middleware.auth import get_optional_user
            # We can't use Depends in a nested call, so save anonymously
            # The report will be linked to user on next authenticated view
            report_id = db_service.save_report(
                user_id=None,
                customer_name=summary.get("customer_name", ""),
                score=score,
                language=lang,
                letter_text=summary.get("letter", ""),
                issues=summary.get("issues", []),
                general_health=health,
            )
            summary["report_id"] = report_id
        except Exception as db_err:
            logger.error("Failed to save report: %s", db_err)

        return summary

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse credit report: {str(e)}")
    finally:
        if tmp_path:
            remove_temp_file(tmp_path)

@app.post("/api/download")
def download_letter(letter_data: dict, background_tasks: BackgroundTasks):
    """
    Generate and download the credit analysis letter as a PDF.
    
    letter_data should contain:
    - letter: The letter text
    - language: Language code
    - score: Credit score
    - customer_name: Customer name
    """
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        create_letter_pdf(letter_data, tmp_path)

        customer_name = letter_data.get("customer_name", "Customer").replace(" ", "_")
        date_str = datetime.now().strftime("%Y%m%d")

        background_tasks.add_task(remove_temp_file, tmp_path)

        return FileResponse(
            path=tmp_path,
            filename=f"CLYR_Letter_{customer_name}_{date_str}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        remove_temp_file(tmp_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate letter PDF: {str(e)}")


@app.get("/test", response_class=HTMLResponse)
async def test_dashboard():
    """Serve the test dashboard for end-to-end testing."""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_dashboard.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return f.read()


# Serve the frontend production build
from fastapi import Request
from pathlib import Path

# Project root is 3 levels up from this file: backend/app/main.py -> app -> backend -> CLYR
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.normpath(os.path.join(_PROJECT_ROOT, "frontend", "dist"))
FRONTEND_INDEX = Path(FRONTEND_DIST) / "index.html"

# Mount static assets (must be before catch-all)
assets_dir = os.path.join(FRONTEND_DIST, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Catch-all route for SPA — serve index.html for any non-API, non-asset route
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Never intercept API, docs, test, or openapi routes
    if full_path.startswith("api/") or full_path.startswith("test") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
        raise HTTPException(status_code=404, detail="Not Found")
    # Serve index.html for root and all SPA routes
    if FRONTEND_INDEX.exists():
        return HTMLResponse(content=FRONTEND_INDEX.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Frontend not built")
