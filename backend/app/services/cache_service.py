import json
import hashlib
from redis.asyncio import Redis
from app.core.config import settings
from app.core.logging_config import logger

class CacheService:
    def __init__(self):
        self.redis: Redis | None = None

    async def connect(self):
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("redis_connected")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get_pipeline_cache(self, key: str) -> dict | None:
        data = await self.redis.get(f"pipeline:{key}")
        return json.loads(data) if data else None

    async def cache_pipeline_result(self, key: str, data: dict, ttl: int = 3600):
        await self.redis.setex(f"pipeline:{key}", ttl, json.dumps(data))

    async def invalidate_job_cache(self, job_id: str):
        await self.redis.delete(f"pipeline:{job_id}")

    async def get_llm_cache(self, prompt_hash: str) -> str | None:
        return await self.redis.get(f"llm:{prompt_hash}")

    async def cache_llm_response(self, prompt_hash: str, response: str, ttl: int = 86400):
        await self.redis.setex(f"llm:{prompt_hash}", ttl, response)

    async def publish_progress(self, job_id: str, stage: str, stage_number: int, total_stages: int, progress: int, message: str):
        event = json.dumps({"stage": stage, "stage_number": stage_number, "total_stages": total_stages, "progress": progress, "message": message})
        await self.redis.publish(f"job:{job_id}:progress", f"event: progress\ndata: {event}\n\n")

    async def publish_complete(self, job_id: str, tkp_url: str):
        event = json.dumps({"job_id": job_id, "tkp_url": tkp_url})
        await self.redis.publish(f"job:{job_id}:progress", f"event: complete\ndata: {event}\n\n")

    async def publish_error(self, job_id: str, stage: str, error: str):
        event = json.dumps({"stage": stage, "error": error})
        await self.redis.publish(f"job:{job_id}:progress", f"event: error\ndata: {event}\n\n")

cache_service = CacheService()
