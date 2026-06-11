from fastapi import APIRouter
from app.services.summary_service import summarize_repository

router = APIRouter()


@router.get("/summarize-repository")
def summarize(repo_name: str):
    return {
        "summary": summarize_repository(repo_name)
    }