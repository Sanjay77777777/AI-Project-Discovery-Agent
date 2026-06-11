from git import Repo
from app.config import REPOSITORIES_DIR


def clone_repository(repo_url: str):

    repo_name = repo_url.rstrip("/").split("/")[-1]

    clone_path = REPOSITORIES_DIR / repo_name

    Repo.clone_from(
        repo_url,
        clone_path
    )

    return {
        "status": "success",
        "repository": repo_name,
        "path": str(clone_path)
    }