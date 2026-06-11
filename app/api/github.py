from typing import List

from fastapi import APIRouter

from app.models.repository import Repository
from app.services.github_service import search_repositories

router = APIRouter()


@router.get(
    "/search-repositories",
    response_model=List[Repository]
)
def search_repo(query: str):
    return search_repositories(query)