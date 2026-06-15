import logging
from ollama import chat, ResponseError
from app.config import LLM_MODEL, LLM_TIMEOUT

logger = logging.getLogger(__name__)


def ask_llm(prompt: str, system: str | None = None):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = chat(model=LLM_MODEL, messages=messages, options={"num_predict": 2048})
        return response["message"]["content"]
    except ResponseError as e:
        if e.status_code == 404:
            logger.error("LLM model '%s' not found: %s", LLM_MODEL, e)
            raise RuntimeError(f"LLM model '{LLM_MODEL}' not found") from e
        logger.error("LLM response error (status %s): %s", e.status_code, e)
        raise RuntimeError(f"LLM service error: {e}") from e
    except ConnectionError as e:
        logger.error("LLM connection failed: %s", e)
        raise RuntimeError("LLM service unavailable") from e
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        raise RuntimeError(f"LLM call failed: {e}") from e