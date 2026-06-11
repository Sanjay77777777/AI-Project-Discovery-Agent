from fastapi import APIRouter
from app.services.analysis_service import (
    analyze_repository,
    read_readme
)

router = APIRouter()


@router.get("/analyze-repository")
def analyze(repo_name: str):
    return analyze_repository(repo_name)
@router.get("/read-readme")
def get_readme(repo_name: str):
    return read_readme(repo_name)