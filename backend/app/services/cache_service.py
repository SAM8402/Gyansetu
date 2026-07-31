import asyncio
import json
import time

from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging_config import logger


class InMemoryPubSub:
    def __init__(self, broker):
        self.broker = broker
        self.queue = asyncio.Queue()
        self.channels = set()

    async def subscribe(self, channel: str):
        self.channels.add(channel)
        self.broker._add_subscriber(channel, self)

    async def unsubscribe(self, channel: str):
        self.channels.discard(channel)
        self.broker._remove_subscriber(channel, self)

    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        try:
            msg = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return {"type": "message", "data": msg}
        except asyncio.TimeoutError:
            return None


class InMemoryRedis:
    """Pure-Python in-memory Redis emulator for 100% free serverless/container deployments.

    NOTE: In-memory pub/sub channels and job status keys live in ONE process. Run
    uvicorn with a single worker when REDIS_URL is empty; for multi-worker
    deployments configure an external Redis so SSE progress and status survive
    across workers.
    """

    def __init__(self):
        self._kv = {}
        self._subscribers = {}

    def _add_subscriber(self, channel, pubsub):
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        self._subscribers[channel].add(pubsub)

    def _remove_subscriber(self, channel, pubsub):
        if channel in self._subscribers:
            self._subscribers[channel].discard(pubsub)

    async def get(self, key: str):
        if key in self._kv:
            val, exp = self._kv[key]
            if exp is None or exp > time.time():
                return val
            else:
                del self._kv[key]
        return None

    async def setex(self, key: str, ttl: int, value: str):
        exp = time.time() + ttl if ttl > 0 else None
        self._kv[key] = (value, exp)

    async def set(self, key: str, value: str, ex: int | None = None):
        exp = time.time() + ex if ex else None
        self._kv[key] = (value, exp)

    async def delete(self, key: str):
        self._kv.pop(key, None)

    async def publish(self, channel: str, message: str):
        subs = self._subscribers.get(channel, set())
        for sub in list(subs):
            await sub.queue.put(message)
        return len(subs)

    def pubsub(self):
        return InMemoryPubSub(self)

    async def ping(self):
        return True

    async def close(self):
        pass


class CacheService:
    def __init__(self):
        self.redis = None
        self._fake_server = None

    def _in_memory_backend(self):
        """Return a fakeredis-backed in-memory Redis (shared FakeServer), or the
        dependency-free InMemoryRedis if fakeredis is not installed."""
        try:
            from fakeredis import FakeServer
            from fakeredis.aioredis import FakeRedis
        except ImportError:
            return InMemoryRedis()
        if self._fake_server is None:
            self._fake_server = FakeServer()
        return FakeRedis(decode_responses=True, server=self._fake_server)

    async def connect(self):
        if self.redis is not None:
            return
        if not settings.REDIS_URL.strip():
            self.redis = self._in_memory_backend()
            logger.info("redis_not_configured_using_in_memory", backend=type(self.redis).__name__)
            return
        try:
            r = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await asyncio.wait_for(r.ping(), timeout=1.5)
            self.redis = r
            logger.info("redis_connected_external", url=settings.REDIS_URL)
        except Exception as e:
            logger.info("redis_external_unavailable_using_in_memory", error=str(e), backend=type(self._in_memory_backend()).__name__)
            self.redis = self._in_memory_backend()

    async def disconnect(self):
        if self.redis:
            try:
                await asyncio.wait_for(self.redis.close(), timeout=2.0)
            except Exception:
                pass

    async def _call(self, method_name: str, *args, **kwargs):
        if not self.redis:
            self.redis = self._in_memory_backend()
        try:
            fn = getattr(self.redis, method_name)
            return await asyncio.wait_for(fn(*args, **kwargs), timeout=3.0)
        except Exception as e:
            logger.warning("redis_call_error_fallback_to_memory", error=str(e), backend=type(self._in_memory_backend()).__name__)
            self.redis = self._in_memory_backend()
            fn = getattr(self.redis, method_name)
            return await asyncio.wait_for(fn(*args, **kwargs), timeout=3.0)

    async def get_pipeline_cache(self, key: str) -> dict | None:
        data = await self._call("get", f"pipeline:{key}")
        return json.loads(data) if data else None

    async def cache_pipeline_result(self, key: str, data: dict, ttl: int = 3600):
        await self._call("set", f"pipeline:{key}", json.dumps(data), ex=ttl)

    async def invalidate_job_cache(self, job_id: str):
        await self._call("delete", f"pipeline:{job_id}")

    async def get_llm_cache(self, prompt_hash: str) -> str | None:
        return await self._call("get", f"llm:{prompt_hash}")

    async def cache_llm_response(self, prompt_hash: str, response: str, ttl: int = 86400):
        await self._call("set", f"llm:{prompt_hash}", response, ex=ttl)

    async def publish_progress(self, job_id: str, stage: str, stage_number: int, total_stages: int, progress: int, message: str):
        event = json.dumps({"stage": stage, "stage_number": stage_number, "total_stages": total_stages, "progress": progress, "message": message})
        await self._call("publish", f"job:{job_id}:progress", f"event: progress\ndata: {event}\n\n")

    async def publish_complete(self, job_id: str, tkp_url: str):
        event = json.dumps({"job_id": job_id, "tkp_url": tkp_url, "done": True})
        await self._call("set", f"job:{job_id}:status", "completed", ex=3600)
        await self._call("publish", f"job:{job_id}:progress", f"event: complete\ndata: {event}\n\n")

    async def publish_error(self, job_id: str, stage: str, error: str):
        event = json.dumps({"stage": stage, "error": error})
        await self._call("set", f"job:{job_id}:status", "failed", ex=3600)
        await self._call("publish", f"job:{job_id}:progress", f"event: error\ndata: {event}\n\n")

cache_service = CacheService()
