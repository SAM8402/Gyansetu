from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.cache_service import cache_service
from app.utils.sse import sse_progress_generator

router = APIRouter(prefix="/api", tags=["stream"])


@router.get("/stream/{job_id}")
async def stream_progress(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return StreamingResponse(
        sse_progress_generator(job_id, cache_service.redis),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
