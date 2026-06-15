from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

REPOSITORIES_DIR = BASE_DIR / "repositories"
VECTORDB_DIR = BASE_DIR / "vectordb"
LOGS_DIR = BASE_DIR / "logs"

IGNORE_PATTERNS = (
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".egg-info",
    ".pytest_cache",
    ".coverage",
)

SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".md",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
)

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200