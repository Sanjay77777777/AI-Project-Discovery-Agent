import logging
import re
from urllib.parse import urlparse
from git import Repo
from app.config import REPOSITORIES_DIR, CLONE_TIMEOUT, MAX_REPO_SIZE_MB

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}


def validate_repo_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed."
        )
    if not parsed.netloc:
        raise ValueError("Invalid repository URL: no hostname found")
    return url


def sanitize_repo_name(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    if not name:
        raise ValueError("Could not determine repository name from URL")
    return name


def check_disk_space():
    try:
        import shutil
        total, used, free = shutil.disk_usage(REPOSITORIES_DIR)
        free_mb = free / (1024 * 1024)
        if free_mb < MAX_REPO_SIZE_MB:
            raise OSError(
                f"Insufficient disk space: {free_mb:.0f} MB free, "
                f"{MAX_REPO_SIZE_MB} MB required"
            )
    except OSError as e:
        raise


def clone_repository(repo_url: str):
    try:
        repo_url = validate_repo_url(repo_url)
    except ValueError as e:
        raise ValueError(str(e))

    repo_name = sanitize_repo_name(repo_url)
    clone_path = REPOSITORIES_DIR / repo_name

    if clone_path.exists():
        raise FileExistsError(f"Repository '{repo_name}' already exists")

    check_disk_space()

    logger.info("Cloning repository '%s' from %s", repo_name, repo_url)
    try:
        Repo.clone_from(
            repo_url,
            clone_path,
            timeout=CLONE_TIMEOUT,
            depth=1,
            single_branch=True,
        )
    except Exception as e:
        logger.error("Clone failed for '%s': %s", repo_name, e)
        raise RuntimeError(f"Failed to clone repository '{repo_name}'") from e

    logger.info("Clone completed for '%s'", repo_name)
    return {
        "status": "success",
        "repository": repo_name,
    }