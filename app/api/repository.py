from fastapi import APIRouter
from app.services.repository_service import clone_repository

router = APIRouter()


@router.get("/clone-repository")
def clone_repo(url: str):
    return clone_repository(url)