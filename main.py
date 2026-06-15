from fastapi import FastAPI
from app.api.home import router as home_router
from app.api.health import router as health_router
from app.api.config_test import router as config_router
from app.api.github import router as github_router
from app.api.ollama import router as ollama_router
from app.api.recommendation import router as recommendation_router
from app.api.repository import router as repository_router
from app.api.analysis import router as analysis_router
from app.api.summary import router as summary_router
from app.api.setup_guide import (
    router as setup_guide_router
)
from app.api.rag import rag_router
app = FastAPI()

app.include_router(home_router)
app.include_router(health_router)
app.include_router(config_router)
app.include_router(github_router)
app.include_router(ollama_router)
app.include_router(recommendation_router)
app.include_router(repository_router)
app.include_router(analysis_router)
app.include_router(summary_router)
app.include_router(setup_guide_router)
app.include_router(rag_router)