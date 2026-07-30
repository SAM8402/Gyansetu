import asyncio
import json
from collections.abc import AsyncGenerator

from app.core.logging_config import logger


async def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def sse_progress_generator(
    job_id: str, redis_client
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE progress messages for a given job.

    Listens on a Redis pubsub channel (``job:{job_id}:progress``) and
    stops when the job's status is ``completed`` or ``failed``.
    Falls back to database polling if Redis is unavailable or fails.
    """
    if redis_client:
        pubsub = None
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"job:{job_id}:progress")

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message.get("data") is not None:
                    raw_data = message["data"]
                    text = raw_data.decode("utf-8") if isinstance(raw_data, bytes) else str(raw_data)
                    yield text if text.endswith("\n\n") else f"{text}\n\n"

                try:
                    status = await redis_client.get(f"job:{job_id}:status")
                    if status:
                        status_str = status.decode("utf-8") if isinstance(status, bytes) else str(status)
                        if status_str in ("completed", "failed"):
                            break
                except Exception:  # noqa: BLE001
                    logger.warning("sse_status_check_failed", job_id=job_id)

                await asyncio.sleep(0.5)
        except Exception as e:  # noqa: BLE001
            logger.warning("sse_redis_error_falling_back", job_id=job_id, error=str(e))
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe(f"job:{job_id}:progress")
                except Exception:  # noqa: BLE001
                    logger.warning("sse_unsubscribe_failed", job_id=job_id)
    else:
        # Fallback to DB polling if Redis is not connected
        from sqlalchemy import select

        from app.db.session import async_session
        from app.models.job import Job

        last_stage = -1
        while True:
            try:
                async with async_session() as db:
                    res = await db.execute(select(Job).where(Job.id == job_id))
                    job = res.scalar_one_or_none()
                    if job:
                        if job.current_stage != last_stage:
                            last_stage = job.current_stage
                            yield await sse_event("progress", {
                                "stage_number": job.current_stage,
                                "total_stages": 10,
                                "status": job.status,
                                "progress": int((job.current_stage / 10) * 100),
                                "message": f"Stage {job.current_stage}/10"
                            })
                        if job.status in ("completed", "failed"):
                            if job.status == "completed":
                                yield await sse_event("complete", {
                                    "job_id": job_id,
                                    "tkp_url": job.tkp_path,
                                    "done": True
                                })
                            else:
                                yield await sse_event("error", {
                                    "error": job.error_message or "Pipeline execution failed",
                                    "done": True
                                })
                            break
            except Exception as e:  # noqa: BLE001
                logger.error("sse_db_fallback_error", error=str(e))
            await asyncio.sleep(1.0)

