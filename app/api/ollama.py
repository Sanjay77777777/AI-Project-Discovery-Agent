from fastapi import APIRouter
from app.services.ollama_service import ask_llm

router = APIRouter()


@router.get("/ask-llm")
def ask(prompt: str):
    return {
        "response": ask_llm(prompt)
    }