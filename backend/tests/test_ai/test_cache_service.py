import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from fakeredis.aioredis import FakeRedis

from app.services.cache_service import CacheService, InMemoryRedis


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.mark.asyncio
async def test_connect(mock_redis):
    with (
        patch("app.services.cache_service.settings.REDIS_URL", "redis://test:6379/0"),
        patch("app.services.cache_service.Redis.from_url", return_value=mock_redis),
    ):
        svc = CacheService()
        await svc.connect()
        assert svc.redis is mock_redis


@pytest.mark.asyncio
async def test_connect_without_redis_url_uses_fakeredis():
    with patch("app.services.cache_service.settings.REDIS_URL", ""):
        svc = CacheService()
        await svc.connect()
        assert isinstance(svc.redis, FakeRedis)
        assert await svc.redis.ping() is True


@pytest.mark.asyncio
async def test_connect_falls_back_to_in_memory_without_fakeredis():
    with (
        patch("app.services.cache_service.settings.REDIS_URL", ""),
        patch.dict("sys.modules", {"fakeredis.aioredis": None}),
    ):
        svc = CacheService()
        await svc.connect()
        assert isinstance(svc.redis, InMemoryRedis)
        assert await svc.redis.ping() is True


@pytest.mark.asyncio
async def test_fakeredis_pubsub_roundtrip():
    with patch("app.services.cache_service.settings.REDIS_URL", ""):
        svc = CacheService()
        await svc.connect()
        pubsub = svc.redis.pubsub()
        await pubsub.subscribe("job:job-1:progress")
        await asyncio.sleep(0.2)
        await svc.publish_progress("job-1", "testing", 2, 10, 50, "half way")
        msg = None
        for _ in range(10):
            msg = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=0.3
            )
            if msg is not None:
                break
        assert msg is not None
        assert "event: progress" in str(msg["data"])
        await pubsub.unsubscribe("job:job-1:progress")


@pytest.mark.asyncio
async def test_disconnect(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.disconnect()
    mock_redis.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_no_redis():
    svc = CacheService()
    await svc.disconnect()


@pytest.mark.asyncio
async def test_get_pipeline_cache_hit(mock_redis):
    mock_redis.get.return_value = '{"data": "value"}'
    svc = CacheService()
    svc.redis = mock_redis
    result = await svc.get_pipeline_cache("key1")
    assert result == {"data": "value"}
    mock_redis.get.assert_awaited_once_with("pipeline:key1")


@pytest.mark.asyncio
async def test_get_pipeline_cache_miss(mock_redis):
    mock_redis.get.return_value = None
    svc = CacheService()
    svc.redis = mock_redis
    result = await svc.get_pipeline_cache("key1")
    assert result is None


@pytest.mark.asyncio
async def test_cache_pipeline_result(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.cache_pipeline_result("key1", {"data": "value"}, ttl=7200)
    mock_redis.set.assert_awaited_once_with(
        "pipeline:key1", '{"data": "value"}', ex=7200
    )


@pytest.mark.asyncio
async def test_invalidate_job_cache(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.invalidate_job_cache("job-1")
    mock_redis.delete.assert_awaited_once_with("pipeline:job-1")


@pytest.mark.asyncio
async def test_get_llm_cache_hit(mock_redis):
    mock_redis.get.return_value = "cached response"
    svc = CacheService()
    svc.redis = mock_redis
    result = await svc.get_llm_cache("abc123")
    assert result == "cached response"
    mock_redis.get.assert_awaited_once_with("llm:abc123")


@pytest.mark.asyncio
async def test_cache_llm_response(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.cache_llm_response("abc123", "response text", ttl=43200)
    mock_redis.set.assert_awaited_once_with(
        "llm:abc123", "response text", ex=43200
    )


@pytest.mark.asyncio
async def test_publish_progress(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.publish_progress("job-1", "testing", 2, 10, 50, "half way")
    expected_data = json.dumps({
        "stage": "testing",
        "stage_number": 2,
        "total_stages": 10,
        "progress": 50,
        "message": "half way",
    })
    expected_msg = f"event: progress\ndata: {expected_data}\n\n"
    mock_redis.publish.assert_awaited_once_with("job:job-1:progress", expected_msg)


@pytest.mark.asyncio
async def test_publish_complete(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.publish_complete("job-1", "/api/jobs/job-1/tkp")
    expected_data = json.dumps({"job_id": "job-1", "tkp_url": "/api/jobs/job-1/tkp", "done": True})
    expected_msg = f"event: complete\ndata: {expected_data}\n\n"
    mock_redis.publish.assert_awaited_once_with("job:job-1:progress", expected_msg)


@pytest.mark.asyncio
async def test_publish_error(mock_redis):
    svc = CacheService()
    svc.redis = mock_redis
    await svc.publish_error("job-1", "testing", "something broke")
    expected_data = json.dumps({"stage": "testing", "error": "something broke"})
    expected_msg = f"event: error\ndata: {expected_data}\n\n"
    mock_redis.publish.assert_awaited_once_with("job:job-1:progress", expected_msg)
