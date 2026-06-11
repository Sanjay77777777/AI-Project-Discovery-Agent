from fastapi import APIRouter
from app.config import REPOSITORIES_DIR

router = APIRouter()

@router.get("/config-test")
def config_test():
    return {
        "repositories_path": str(REPOSITORIES_DIR)
    }