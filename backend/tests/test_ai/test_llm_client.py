from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.llm_client import generate_json, get_llm, hash_prompt
from app.core.config import settings


@pytest.fixture(autouse=True)
def clear_llm_cache():
    from app.ai.llm_client import _llm_instances
    from app.services.cache_service import cache_service

    _llm_instances.clear()
    cache_service.redis = None
    cache_service._fake_server = None


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm


class TestGetLLM:
    async def test_returns_cached_instance(self, mock_llm):
        with patch("app.ai.llm_client._build_llm", return_value=mock_llm):
            from app.ai.llm_client import _llm_instances
            _llm_instances["gemini-2.0-flash:0.3"] = mock_llm
            result = await get_llm()
            assert result is mock_llm

    async def test_creates_new_instance(self, mock_llm):
        with (
            patch("app.ai.llm_client._build_llm", return_value=mock_llm),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
        ):
            result = await get_llm()
            assert result is mock_llm

    async def test_raises_without_api_keys(self):
        with patch.object(settings, "GOOGLE_API_KEY", ""):
            with pytest.raises(ValueError, match="No Google API keys configured"):
                await get_llm()


class TestGenerateJson:
    async def test_success_with_first_model(self, mock_llm):
        mock_llm.ainvoke.return_value.content = '{"key": "value"}'
        with (
            patch("app.ai.llm_client._build_llm", return_value=mock_llm),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "model-1"),
        ):
            result = await generate_json("test prompt")
            assert result == {"key": "value"}

    async def test_falls_through_models_on_failure(self, mock_llm):
        mock_llm.ainvoke.side_effect = [
            Exception("model-1 failed"),
            type("Response", (), {"content": '{"ok": true}'})(),
        ]
        with (
            patch("app.ai.llm_client._build_llm", return_value=mock_llm),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "model-1,model-2"),
        ):
            result = await generate_json("test prompt")
            assert result == {"ok": True}

    async def test_cycles_api_keys(self, mock_llm):
        mock_llm.ainvoke.side_effect = [Exception("fail"), type("Response", (), {"content": '{"ok": true}'})()]
        call_args = []
        def build_side_effect(model, key, temp):
            call_args.append((model, key))
            return mock_llm

        with (
            patch("app.ai.llm_client._build_llm", side_effect=build_side_effect),
            patch.object(settings, "GOOGLE_API_KEY", "key1,key2"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "m1,m2"),
        ):
            await generate_json("test", temperature=0.5)
            assert call_args[0][1] == "key1"
            assert call_args[1][1] == "key2"

    async def test_raises_when_all_models_fail(self, mock_llm):
        mock_llm.ainvoke.side_effect = Exception("always fails")
        with (
            patch("app.ai.llm_client._build_llm", return_value=mock_llm),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "m1"),
        ):
            with pytest.raises(Exception, match="always fails"):
                await generate_json("test")

    async def test_strips_markdown_json_fence(self, mock_llm):
        mock_llm.ainvoke.return_value.content = '```json\n{"key": "value"}\n```'
        with (
            patch("app.ai.llm_client._build_llm", return_value=mock_llm),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "m1"),
        ):
            result = await generate_json("test")
            assert result == {"key": "value"}

    async def test_passes_temperature_and_model(self, mock_llm):
        mock_llm.ainvoke.return_value.content = '{"ok": true}'
        call_kwargs = {}
        def build_side_effect(model, key, temp):
            call_kwargs["model"] = model
            call_kwargs["temp"] = temp
            return mock_llm

        with (
            patch("app.ai.llm_client._build_llm", side_effect=build_side_effect),
            patch.object(settings, "GOOGLE_API_KEY", "key1"),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "custom-model"),
        ):
            await generate_json("test", temperature=0.7, model="custom-model")
            assert call_kwargs["temp"] == 0.7
            assert call_kwargs["model"] == "custom-model"

    async def test_raises_without_api_keys(self):
        with (
            patch.object(settings, "GOOGLE_API_KEY", ""),
            patch.object(settings, "LLM_FALLBACK_CHAIN", "m1"),
        ):
            with pytest.raises(ValueError, match="No Google API keys configured"):
                await generate_json("test")


class TestHashPrompt:
    def test_produces_hex_string(self):
        result = hash_prompt("hello", "gemini-2.0-flash")
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        r1 = hash_prompt("same prompt", "same model")
        r2 = hash_prompt("same prompt", "same model")
        assert r1 == r2

    def test_different_model_different_hash(self):
        r1 = hash_prompt("prompt", "model-a")
        r2 = hash_prompt("prompt", "model-b")
        assert r1 != r2
