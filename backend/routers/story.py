import os
import io
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/api/story", tags=["story"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract plain text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        return f"[Text extraction failed: {e}]"


# ── Schemas ───────────────────────────────────────────────────────────────────

class StoryDraft(BaseModel):
    story_text: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/latest")
async def get_story(current_user: dict = Depends(get_current_user)):
    """Load the user's saved patient story draft."""
    db = get_db()
    story = await db.stories.find_one({"user_email": current_user["email"]})
    if not story:
        return {"story_text": "", "analysis": None}
    story["_id"] = str(story["_id"])
    return story


@router.post("/save-draft")
async def save_draft(data: StoryDraft, current_user: dict = Depends(get_current_user)):
    """Autosave the story text (debounced from frontend)."""
    db = get_db()
    doc = {
        "user_email": current_user["email"],
        "story_text": data.story_text,
        "updated_at": datetime.utcnow().isoformat(),
    }
    await db.stories.update_one(
        {"user_email": current_user["email"]},
        {"$set": doc},
        upsert=True,
    )
    return {"success": True}


@router.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    doctor: str = Form(""),
    specialty: str = Form(""),
    report_type: str = Form("Lab report"),
    report_date: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a PDF report, extract text with PyMuPDF, save metadata to MongoDB.
    Returns the extracted text so the frontend can display it immediately.
    No Cloudinary needed — we store metadata in MongoDB and text inline.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()
    extracted_text = extract_pdf_text(file_bytes)

    db = get_db()
    doc = {
        "user_email": current_user["email"],
        "filename": file.filename,
        "doctor": doctor,
        "specialty": specialty,
        "report_type": report_type,
        "report_date": report_date or datetime.utcnow().strftime("%Y-%m-%d"),
        "extracted_text": extracted_text,
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    result = await db.reports.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "filename": file.filename,
        "extracted_text": extracted_text,
        "report_type": report_type,
        "cloudinary_url": None,   # not using Cloudinary — text stored in DB
    }


@router.get("/reports")
async def get_reports(current_user: dict = Depends(get_current_user)):
    """List all uploaded reports for the user."""
    db = get_db()
    cursor = db.reports.find(
        {"user_email": current_user["email"]},
        sort=[("uploaded_at", -1)],
    ).limit(20)

    reports = []
    async for r in cursor:
        r["_id"] = str(r["_id"])
        reports.append(r)
    return reports
