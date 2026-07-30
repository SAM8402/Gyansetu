from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.job import JobResponse, JobListResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job)
        .where(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return JobListResponse(
        jobs=[
            JobResponse(
                id=j.id,
                status=j.status,
                current_stage=j.current_stage,
                file_name=j.file_name,
                error_message=j.error_message,
                created_at=j.created_at,
                completed_at=j.completed_at,
                tkp_url=f"/api/jobs/{j.id}/tkp" if j.tkp_path else None,
            )
            for j in jobs
        ],
        total=len(jobs),
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(
        id=job.id,
        status=job.status,
        current_stage=job.current_stage,
        file_name=job.file_name,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        tkp_url=f"/api/jobs/{job.id}/tkp" if job.tkp_path else None,
    )


@router.get("/{job_id}/tkp")
async def download_tkp(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job or not job.tkp_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TKP not found")
    from fastapi.responses import FileResponse

    return FileResponse(
        job.tkp_path,
        media_type="application/json",
        filename=f"tkp_{job_id}.json",
    )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    await db.delete(job)
    return {"message": "Job deleted"}
