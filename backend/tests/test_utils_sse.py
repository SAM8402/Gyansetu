import json
import pytest

from app.utils.sse import sse_event


@pytest.mark.asyncio
class TestSSEEvent:
    async def test_sse_event_format(self):
        result = await sse_event("progress", {"stage": 3, "message": "testing"})
        assert result == "event: progress\ndata: {\"stage\": 3, \"message\": \"testing\"}\n\n"

    async def test_sse_event_empty_data(self):
        result = await sse_event("complete", {})
        assert result.startswith("event: complete")
        assert result.endswith("\n\n")

    async def test_sse_event_with_nested_data(self):
        data = {"job_id": "j1", "scores": [0.9, 0.85]}
        result = await sse_event("result", data)
        parsed = json.loads(result.split("data: ")[1].strip())
        assert parsed["job_id"] == "j1"
        assert parsed["scores"] == [0.9, 0.85]
