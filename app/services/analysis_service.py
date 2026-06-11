from pathlib import Path
from app.config import REPOSITORIES_DIR


def analyze_repository(repo_name: str):

    repo_path = REPOSITORIES_DIR / repo_name

    python_files = list(repo_path.rglob("*.py"))

    return {
    "repository": repo_name,

    "readme_found":
        (repo_path / "README.md").exists(),

    "requirements_found":
        (repo_path / "requirements.txt").exists(),

    "pyproject_found":
        (repo_path / "pyproject.toml").exists(),

    "package_json_found":
        (repo_path / "package.json").exists(),

    "dockerfile_found":
        (repo_path / "Dockerfile").exists(),

    "docker_compose_found":
        (repo_path / "docker-compose.yml").exists(),

    "python_files":
        len(python_files),
        
    "tests_found":
        (repo_path / "tests").exists(),

    "docs_found":
        (repo_path / "docs").exists(),
}
def read_readme(repo_name: str):

    repo_path = REPOSITORIES_DIR / repo_name

    readme_path = repo_path / "README.md"

    if not readme_path.exists():
        return {
            "error": "README.md not found"
        }

    content = readme_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    return {
        "repository": repo_name,
        "content": content
    }