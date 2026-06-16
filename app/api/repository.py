import logging
from fastapi import APIRouter, HTTPException, status
from app.services.repository_service import clone_repository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/clone-repository")
def clone_repo(url: str):
    try:
        return clone_repository(url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to clone repository",
        )
    except Exception as e:
        logger.error("Clone failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone repository",
        )