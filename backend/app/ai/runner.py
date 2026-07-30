from datetime import datetime, timezone

from sqlalchemy import select

from app.core.logging_config import logger
from app.services.cache_service import cache_service
from app.ai.pipeline import build_pipeline, create_initial_state


async def run_pipeline(job_id: str, file_path: str, config: dict):
    from app.db.session import async_session
    from app.models.job import Job

    try:
        state = create_initial_state()
        state["job_id"] = job_id
        state["file_path"] = file_path
        state["config"] = config
        pipeline = build_pipeline()

        async with async_session() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = "processing"
                await db.commit()

        await cache_service.publish_progress(
            job_id, "document-intelligence", 1, 10, 0, "Starting pipeline..."
        )

        final_state = await pipeline.ainvoke(state)

        async with async_session() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = "completed"
                job.current_stage = 10
                job.tkp_path = final_state.get("result", {}).get("tkp_path", "")
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

        tkp_url = f"/api/jobs/{job_id}/tkp"
        if final_state.get("result", {}).get("tkp_path"):
            tkp_url = f"/api/jobs/{job_id}/tkp"

        await cache_service.publish_complete(job_id, tkp_url)
        logger.info("pipeline_complete", job_id=job_id)

    except Exception as e:
        logger.error("pipeline_error", job_id=job_id, error=str(e))
        async with async_session() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()
        await cache_service.publish_error(job_id, "pipeline", str(e))
