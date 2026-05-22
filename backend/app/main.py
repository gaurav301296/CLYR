import os
import tempfile
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

from app.utils.parser import extract_pdf_text
from app.services.llm_service import generate_credit_summary
from app.utils.pdf_generator import create_report_pdf
from app.utils.logging_config import logger
from app.utils.sanitization import sanitize_pdf_text, sanitize_filename
from app.routes.user_routes import router as user_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

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
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user routes
app.include_router(user_router)

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

class IssueModel(BaseModel):
    account: str
    type: str
    details: str
    action: str
    impact: str

class TimelineModel(BaseModel):
    phase: str
    task: str
    status: str

class CreditReportData(BaseModel):
    score: int
    customer_name: str
    general_health: str
    issues: List[IssueModel]
    action_steps: List[str]
    timeline: List[TimelineModel]
    language: str = "en"

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
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Write uploaded file content to a temporary location
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
            if len(content) < 100:
                raise HTTPException(status_code=400, detail="File is empty or too small to be a valid PDF.")
            # Check PDF magic bytes
            if not content[:4].startswith(PDF_MAGIC):
                raise HTTPException(status_code=400, detail="File is not a valid PDF.")
            tmp.write(content)
            tmp_path = tmp.name
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    try:
        # Extract text from the PDF
        raw_text = extract_pdf_text(tmp_path)

        # Synthesize plain English report structure via rules / LLM
        summary = generate_credit_summary(raw_text)
        return summary

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse credit report: {str(e)}")
    finally:
        # Cleanup upload temp file
        if tmp_path:
            remove_temp_file(tmp_path)

@app.post("/api/download")
def download_report(data: CreditReportData, background_tasks: BackgroundTasks):
    # Create temp file for PDF compilation
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd) # Close file descriptor immediately to avoid lock on Windows
    
    try:
        # Generate the report PDF
        create_report_pdf(data.model_dump(), tmp_path, language=data.language)
        
        # Enqueue removal of temp file as background task
        background_tasks.add_task(remove_temp_file, tmp_path)
        
        return FileResponse(
            path=tmp_path,
            filename=f"CLYR_Roadmap_{data.customer_name.replace(' ', '_')}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        remove_temp_file(tmp_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate report PDF: {str(e)}")
