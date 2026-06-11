from fastapi import APIRouter
from app.services.recommendation_service import recommend_repository

router = APIRouter()


@router.get("/recommend-project")
def recommend(query: str):
    return {
        "result": recommend_repository(query)
    }