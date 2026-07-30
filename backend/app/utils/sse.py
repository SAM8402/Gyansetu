import json
from typing import AsyncGenerator


async def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def sse_progress_generator(
    job_id: str, redis_client
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE progress messages for a given job.

    Listens on a Redis pubsub channel (``job:{job_id}:progress``) and
    stops when the job's status in Redis is ``completed`` or ``failed``.
    """
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"job:{job_id}:progress")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                yield message["data"].decode()

            status = await redis_client.get(f"job:{job_id}:status")
            if status and status.decode() in ("completed", "failed"):
                break
    finally:
        await pubsub.unsubscribe(f"job:{job_id}:progress")
