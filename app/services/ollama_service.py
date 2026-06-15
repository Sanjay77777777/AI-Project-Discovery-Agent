from ollama import chat
from app.config import LLM_MODEL


def ask_llm(prompt: str, system: str | None = None):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = chat(model=LLM_MODEL, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e