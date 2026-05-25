"""
CLYR v2 — Report Routes (SQLite)
Core of the app: upload credit report PDFs, analyze with LLM,
store in SQLite, and serve back with PDF generation.

Routes:
  POST /api/reports/upload       — Upload PDF, analyze, save to SQLite
  GET  /api/reports              — List authenticated user's reports
  GET /api/reports/:id           — Get specific report (ownership check)
  GET /api/pdf/preview/:id       — Watermarked preview PDF
  GET /api/pdf/serve-preview/:id — Serve preview PDF file
  GET /api/pdf/download/:id      — Download full PDF (paid check)
"""
import os
import json
import logging
import tempfile
import time
from uuid import uuid4

from fastapi import APIRouter, Request, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse

from app.database import db_insert, db_select, db_update, db_count, get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.utils.parser import extract_pdf_text
from app.services.llm_service import generate_credit_summary
from app.utils.pdf_generator import create_letter_pdf
from app.utils.sanitization import sanitize_filename
from app.config import config
logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])

MAX_UPLOAD_BYTES = config.max_upload_size_mb * 1024 * 1024


def _row_to_report_response(row: dict) -> dict:
    """Convert a DB report row to API response dict."""
    issues_raw = row.get("issues_json") or row.get("issues") or []
    if isinstance(issues_raw, str):
        try:
            issues_raw = json.loads(issues_raw)
        except Exception:
            issues_raw = []

    action_steps_raw = row.get("action_steps_json") or row.get("action_steps") or []
    if isinstance(action_steps_raw, str):
        try:
            action_steps_raw = json.loads(action_steps_raw)
        except Exception:
            action_steps_raw = []

    timeline_raw = row.get("timeline_json") or row.get("timeline") or []
    if isinstance(timeline_raw, str):
        try:
            timeline_raw = json.loads(timeline_raw)
        except Exception:
            timeline_raw = []

    return {
        "id": str(row.get("id", "")),
        "customer_name": str(row.get("customer_name", "")),
        "score": int(row.get("score", 0)),
        "language": str(row.get("language", "en")),
        "letter": str(row.get("letter_text", "")),
        "issues": issues_raw if isinstance(issues_raw, list) else [],
        "action_steps": action_steps_raw if isinstance(action_steps_raw, list) else [],
        "timeline": timeline_raw if isinstance(timeline_raw, list) else [],
        "general_health": str(row.get("general_health", "")),
        "status": str(row.get("status", "completed")),
        "pdf_url": str(row.get("pdf_url", "")),
        "created_at": str(row.get("created_at", "")),
    }


SUPPORTED_LANGUAGES = {'en', 'hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or'}

# ─── Upload Report ────────────────────────────────────────────────────────────

@router.post("/reports/upload")
async def upload_report(
    request: Request,
    file: UploadFile = File(..., description="Credit report PDF file (max 10MB)"),
    lang: str = Query(default="en", max_length=10, description="Language code"),
    user: dict | None = Depends(get_optional_user),
):
    """Upload a credit report PDF, extract text, analyze with LLM, save to SQLite."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")

    safe_name = sanitize_filename(file.filename)
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if not content[:5].startswith(b'%PDF-'):
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {config.max_upload_size_mb} MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    tmp_path = os.path.join(tempfile.gettempdir(), f"clyr_{uuid4().hex}_{safe_name}")
    try:
        with open(tmp_path, "wb") as tmp_f:
            tmp_f.write(content)

        # Extract text
        try:
            raw_text = extract_pdf_text(tmp_path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            raise HTTPException(status_code=422, detail=f"Failed to extract text from PDF: {e}")

        # Analyze with LLM
        try:
            analysis = generate_credit_summary(raw_text, language=lang)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error("LLM analysis failed: %s", e)
            raise HTTPException(status_code=502, detail=f"Analysis service error: {e}")

        # Save to SQLite
        report_id = str(uuid4())
        now = time.time()

        issues = analysis.get("issues", [])
        issues_json = []
        for issue in (issues or []):
            if isinstance(issue, dict):
                issues_json.append({
                    "account": str(issue.get("account", "")),
                    "type": str(issue.get("type", "Yellow")),
                    "details": str(issue.get("details", "")),
                    "impact": str(issue.get("impact", "")),
                    "action": str(issue.get("action", "")),
                })

        timeline = analysis.get("timeline", [])
        timeline_json = []
        for item in (timeline or []):
            if isinstance(item, dict):
                timeline_json.append({
                    "phase": str(item.get("phase", "")),
                    "task": str(item.get("task", "")),
                    "status": str(item.get("status", "Pending")),
                })

        action_steps_flat = [str(s) for s in (analysis.get("action_steps", []) or [])]

        user_id = user["id"] if user else None

        insert_data = {
            "id": report_id,
            "user_id": user_id,
            "customer_name": analysis.get("customer_name", ""),
            "score": analysis.get("score", 600),
            "language": lang,
            "letter_text": analysis.get("letter", ""),
            "issues_json": json.dumps(issues_json, ensure_ascii=False),
            "action_steps_json": json.dumps(action_steps_flat, ensure_ascii=False),
            "timeline_json": json.dumps(timeline_json, ensure_ascii=False),
            "general_health": analysis.get("general_health", ""),
            "status": "completed",
            "pdf_url": "",
            "created_at": now,
            "updated_at": now,
        }

        try:
            db_insert("reports", insert_data)
            logger.info("Report saved: %s (user=%s)", report_id, user_id)
        except Exception as e:
            logger.error("Failed to save report %s: %s", report_id, e)
            raise HTTPException(status_code=502, detail=f"Failed to save report: {e}")

        return _row_to_report_response(insert_data)

    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


# ─── List Reports ─────────────────────────────────────────────────────────────

@router.get("/reports")
async def list_reports(user: dict = Depends(get_current_user)):
    """List all reports for the authenticated user."""
    try:
        reports = db_select("reports", filters={"user_id": user["id"]}, order_by="-created_at")
        return {"reports": [_row_to_report_response(r) for r in reports], "total": len(reports)}
    except Exception as e:
        logger.error("Failed to list reports for user %s: %s", user["id"], e)
        raise HTTPException(status_code=502, detail=f"Failed to fetch reports: {e}")


# ─── Get Report by ID ─────────────────────────────────────────────────────────

@router.get("/reports/{report_id}")
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Get a specific report by ID. Verifies ownership."""
    rows = db_select("reports", filters={"id": report_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    report = rows[0]
    report_owner = report.get("user_id")
    if report_owner and report_owner != user["id"]:
        raise HTTPException(status_code=403, detail="You do not own this report")

    return _row_to_report_response(report)


# ─── PDF Preview ──────────────────────────────────────────────────────────────

@router.get("/pdf/preview/{report_id}")
async def preview_pdf(report_id: str, user: dict = Depends(get_current_user)):
    """Generate a watermarked preview PDF."""
    rows = db_select("reports", filters={"id": report_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    report = rows[0]
    if report.get("user_id") and report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You do not own this report")

    try:
        preview_dir = os.path.join(tempfile.gettempdir(), "clyr_previews")
        os.makedirs(preview_dir, exist_ok=True)
        preview_path = os.path.join(preview_dir, f"preview_{report_id}.pdf")

        letter_data = {
            "letter": report.get("letter_text", ""),
            "language": report.get("language", "en"),
            "score": report.get("score", 0),
            "customer_name": report.get("customer_name", "Customer"),
            "preview": True,
        }

        create_letter_pdf(letter_data, preview_path)

        preview_url = f"/api/pdf/serve-preview/{report_id}"
        db_update("reports", {"pdf_url": preview_url}, {"id": report_id})

        return {"preview_url": preview_url, "report_id": report_id, "message": "Watermarked preview ready"}

    except Exception as e:
        logger.error("PDF preview generation failed for %s: %s", report_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to generate preview PDF: {e}")


# ─── Serve Preview PDF File ───────────────────────────────────────────────────

@router.get("/pdf/serve-preview/{report_id}")
async def serve_preview_file(report_id: str, user: dict = Depends(get_current_user)):
    """Serve the actual preview PDF file."""
    rows = db_select("reports", filters={"id": report_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")
    if rows[0].get("user_id") and rows[0]["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    preview_path = os.path.join(tempfile.gettempdir(), "clyr_previews", f"preview_{report_id}.pdf")
    if not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Preview not generated yet. Call /pdf/preview/:id first.")

    return FileResponse(preview_path, media_type="application/pdf", filename=f"clyr_preview_{report_id}.pdf")


# ─── PDF Download ─────────────────────────────────────────────────────────────

@router.get("/pdf/download/{report_id}")
async def download_pdf(request: Request, report_id: str, user: dict = Depends(get_optional_user)):
    """Download the full (unwatermarked) PDF. Requires a paid order."""
    rows = db_select("reports", filters={"id": report_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    report = rows[0]

    # Check payment status
    if user:
        # Authenticated: check user's paid orders for this report
        paid_orders = db_select("orders", filters={
            "user_id": user["id"],
            "report_id": report_id,
            "status": "paid",
        })
        if not paid_orders:
            paid_orders = db_select("orders", filters={
                "user_id": user["id"],
                "status": "paid",
            })
    else:
        # Anonymous: check any paid order for this report_id
        paid_orders = db_select("orders", filters={
            "report_id": report_id,
            "status": "paid",
        })

    if not paid_orders:
        raise HTTPException(status_code=402, detail="Payment required. Please purchase to download.")

    # Generate full PDF
    try:
        download_dir = os.path.join(tempfile.gettempdir(), "clyr_downloads")
        os.makedirs(download_dir, exist_ok=True)
        download_path = os.path.join(download_dir, f"clyr_{report_id}.pdf")

        letter_data = {
            "letter": report.get("letter_text", ""),
            "language": report.get("language", "en"),
            "score": report.get("score", 0),
            "customer_name": report.get("customer_name", "Customer"),
            "preview": False,
        }

        create_letter_pdf(letter_data, download_path)

        return FileResponse(
            download_path,
            media_type="application/pdf",
            filename=f"clyr_report_{report_id}.pdf",
        )

    except Exception as e:
        logger.error("PDF download generation failed for %s: %s", report_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
