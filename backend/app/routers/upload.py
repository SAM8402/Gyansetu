import asyncio
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.job import Job
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.config import settings
from app.core.logging_config import logger
from app.services.cache_service import cache_service
from app.ai.runner import run_pipeline

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    period_duration: int = Form(40),
    num_periods: int = Form(0),
    doc_type: str = Form("auto"),
    teaching_style: str = Form("Interactive & Activity-Driven"),
    target_language: str = Form("English"),
    board_alignment: str = Form("General"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".pptx", ".txt"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    job_id = str(uuid.uuid4())
    file_path = upload_dir / f"{job_id}{ext}"
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    config = {
        "period_duration": period_duration,
        "num_periods": num_periods,
        "doc_type": doc_type,
        "teaching_style": teaching_style,
        "target_language": target_language,
        "board_alignment": board_alignment,
    }
    job = Job(
        id=job_id,
        user_id=current_user.id,
        status="pending",
        file_name=file.filename,
        file_path=str(file_path),
        config=config,
    )
    db.add(job)
    await db.commit()
    logger.info("job_created", job_id=job_id, file=file.filename)

    # Start the pipeline as a background task
    asyncio.create_task(run_pipeline(job_id, str(file_path), config))

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Document uploaded. Pipeline will start processing.",
    }
