from fastapi import APIRouter

from app.services.setup_guide_service import (
    generate_setup_guide
)

router = APIRouter()


@router.get("/generate-setup-guide")
def setup_guide(repo_name: str):
    return {
        "guide": generate_setup_guide(repo_name)
    }