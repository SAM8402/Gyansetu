import asyncio
import hashlib
import json
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.core.logging_config import logger

_llm_instances = {}


def _build_llm(model: str, api_key: str, temperature: float) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        max_retries=1,
        convert_system_message_to_human=True,
    )


async def get_llm(temperature: float = 0.3, model: Optional[str] = None) -> ChatGoogleGenerativeAI:
    model_name = model or settings.GEMINI_MODEL
    cache_key = f"{model_name}:{temperature}"
    if cache_key in _llm_instances:
        return _llm_instances[cache_key]

    api_keys = settings.api_keys
    if not api_keys:
        raise ValueError("No Google API keys configured")

    llm = _build_llm(model_name, api_keys[0], temperature)
    _llm_instances[cache_key] = llm
    return llm


async def generate_json(prompt: str, temperature: float = 0.3, model: Optional[str] = None) -> dict:
    from app.services.cache_service import cache_service

    base_model = model or settings.GEMINI_MODEL
    p_hash = hash_prompt(prompt, base_model)

    # 1. Ultra-fast Redis/Memory cache check (0.001s response time on cache hit!)
    try:
        cached_str = await cache_service.get_llm_cache(p_hash)
        if cached_str:
            logger.info("llm_cache_hit", hash=p_hash[:8])
            return json.loads(cached_str)
    except Exception:
        pass

    fallback_chain = settings.fallback_models or ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite"]
    models = []
    for m in [base_model] + fallback_chain:
        if m not in models:
            models.append(m)

    api_keys = settings.api_keys
    if not api_keys:
        raise ValueError("No Google API keys configured")

    last_error = None
    for m in models:
        for key in api_keys:
            try:
                logger.info("llm_invoke_attempt", model=m, key_preview=key[:6] if key else "none")
                llm = _build_llm(m, key, temperature)
                response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=25.0)
                raw_content = response.content
                if isinstance(raw_content, list):
                    text = "".join(item if isinstance(item, str) else str(item.get("text", item)) for item in raw_content).strip()
                else:
                    text = str(raw_content).strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    text = text.rsplit("```", 1)[0]
                result = json.loads(text)

                # Cache response for 24h
                try:
                    await cache_service.cache_llm_response(p_hash, json.dumps(result))
                except Exception:
                    pass

                return result
            except Exception as e:
                err_msg = str(e)
                logger.warning("llm_call_attempt_failed", model=m, error=err_msg, key_preview=key[:6] if key else "none")
                last_error = e
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    await asyncio.sleep(0.5)
                continue

    logger.error("llm_all_failed", error=str(last_error), prompt_preview=prompt[:100])
    raise last_error or RuntimeError("No LLM models available")


def hash_prompt(prompt: str, model: str) -> str:
    """Generate a deterministic SHA-256 hash for a prompt+model combination.

    Args:
        prompt: The prompt text.
        model: The model identifier.

    Returns:
        Hex digest string.
    """
    return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()
