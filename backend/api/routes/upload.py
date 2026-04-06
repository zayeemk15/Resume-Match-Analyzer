"""
api/routes/upload.py — POST /api/v1/upload — Pre-upload a resume file
"""
from __future__ import annotations
from pathlib import Path
import uuid
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from backend.db.database import get_db
from backend.db import crud
from backend.core.config import settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_resume(
    resume_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file and get back a file_id to use in subsequent requests.
    Supports PDF, DOCX, and TXT formats up to 10 MB.
    """
    content = await resume_file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 10 MB.")

    file_ext = Path(resume_file.filename or "resume.pdf").suffix.lower()
    if file_ext not in (".pdf", ".docx", ".doc", ".txt"):
        raise HTTPException(400, f"Unsupported file type: {file_ext}. Use PDF, DOCX, or TXT.")

    file_id = str(uuid.uuid4())
    save_path = settings.upload_dir / f"{file_id}{file_ext}"

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    resume_db = await crud.create_resume_file(
        db,
        filename=resume_file.filename or "resume",
        file_size=len(content),
        content_type=resume_file.content_type,
    )

    logger.info("Resume uploaded", file_id=file_id, filename=resume_file.filename)

    return {
        "file_id":  resume_db.id,
        "filename": resume_file.filename,
        "size_kb":  round(len(content) / 1024, 1),
        "message":  "Upload successful. Use file_id with /analyze.",
    }
