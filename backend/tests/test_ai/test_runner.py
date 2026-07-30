import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.runner import run_pipeline


@pytest.mark.asyncio
async def test_run_pipeline_success():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_job = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_job
    mock_session.execute.return_value = mock_result

    mock_pipeline = AsyncMock()
    mock_pipeline.ainvoke.return_value = {
        "current_stage": 11,
        "result": {"tkp_path": "/tmp/test.tkp"},
    }

    with (
        patch("app.db.session.async_session", return_value=mock_session),
        patch("app.ai.runner.build_pipeline", return_value=mock_pipeline),
        patch("app.ai.runner.cache_service", new_callable=AsyncMock) as mock_cache,
    ):
        await run_pipeline("test-id", "/tmp/doc.pdf", {"audience": "students"})

    mock_pipeline.ainvoke.assert_awaited_once()
    assert mock_job.status == "completed"
    assert mock_job.tkp_path == "/tmp/test.tkp"
    assert mock_job.current_stage == 11
    mock_cache.publish_progress.assert_awaited_once()
    mock_cache.publish_complete.assert_awaited_once_with("test-id", "/api/jobs/test-id/tkp")


@pytest.mark.asyncio
async def test_run_pipeline_handles_error():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_job = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_job
    mock_session.execute.return_value = mock_result

    mock_pipeline = AsyncMock()
    mock_pipeline.ainvoke.side_effect = ValueError("pipeline exploded")

    with (
        patch("app.db.session.async_session", return_value=mock_session),
        patch("app.ai.runner.build_pipeline", return_value=mock_pipeline),
        patch("app.ai.runner.cache_service", new_callable=AsyncMock) as mock_cache,
    ):
        await run_pipeline("test-id", "/tmp/doc.pdf", {})

    assert mock_job.status == "failed"
    assert mock_job.error_message == "pipeline exploded"
    mock_cache.publish_error.assert_awaited_once_with("test-id", "pipeline", "pipeline exploded")


@pytest.mark.asyncio
async def test_run_pipeline_handles_missing_job():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    mock_pipeline = AsyncMock()
    mock_pipeline.ainvoke.return_value = {
        "current_stage": 11,
        "result": {"tkp_path": "/tmp/test.tkp"},
    }

    with (
        patch("app.db.session.async_session", return_value=mock_session),
        patch("app.ai.runner.build_pipeline", return_value=mock_pipeline),
        patch("app.ai.runner.cache_service", new_callable=AsyncMock) as mock_cache,
    ):
        await run_pipeline("test-id", "/tmp/doc.pdf", {})

    mock_pipeline.ainvoke.assert_awaited_once()
    mock_cache.publish_complete.assert_awaited_once()
