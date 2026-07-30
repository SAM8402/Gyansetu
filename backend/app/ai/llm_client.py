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
    models = settings.fallback_models or [model or settings.GEMINI_MODEL]
    if model and model not in models:
        models.insert(0, model)

    api_keys = settings.api_keys
    if not api_keys:
        raise ValueError("No Google API keys configured")

    last_error = None
    for i, m in enumerate(models):
        key = api_keys[i % len(api_keys)]
        try:
            llm = _build_llm(m, key, temperature)
            response = await llm.ainvoke(prompt)
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as e:
            logger.warning("llm_fallback", model=m, error=str(e))
            last_error = e

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
