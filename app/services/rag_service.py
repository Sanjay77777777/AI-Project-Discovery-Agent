from pathlib import Path
import os
import uuid
from typing import Generator, List, Dict, Optional

import ollama
import chromadb
from chromadb.config import Settings

from app.config import (
    REPOSITORIES_DIR,
    CHROMADB_PATH,
    IGNORE_PATTERNS,
    SUPPORTED_EXTENSIONS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
)


class DocumentProcessor:
    def __init__(self, repo_name: str):
        self.repo_name = repo_name
        self.repo_path = REPOSITORIES_DIR / repo_name

    def should_ignore_path(self, path: Path) -> bool:
        for part in path.parts:
            if part in IGNORE_PATTERNS:
                return True
        return False

    def get_file_category(self, filepath: str) -> str:
        ext = Path(filepath).suffix.lower()
        docs_exts = {".md", ".txt", ".rst"}
        config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
        if ext in docs_exts:
            return "docs"
        elif ext in config_exts:
            return "config"
        else:
            return "code"

    def walk_repository(self) -> Generator[Path, None, None]:
        if not self.repo_path.exists():
            return
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS]
            for file in files:
                yield Path(root) / file

    def read_file_safe(self, path: Path) -> Optional[str]:
        try:
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                return None
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    def chunk_document(self, content: str, filepath: str) -> List[Dict]:
        chunks = []
        if not content or not content.strip():
            return chunks

        lines = content.splitlines()
        current_chunk = []
        current_size = 0

        for line in lines:
            line_len = len(line) + 1
            if current_size + line_len > CHUNK_SIZE and current_chunk:
                chunk_text = "\n".join(current_chunk)
                chunks.append({
                    "content": chunk_text,
                    "file_path": filepath,
                    "category": self.get_file_category(filepath),
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_number": len(chunks) + 1,
                })
                overlap_lines = []
                overlap_size = 0
                for ol in reversed(current_chunk):
                    ol_len = len(ol) + 1
                    if overlap_size + ol_len > CHUNK_OVERLAP:
                        break
                    overlap_lines.insert(0, ol)
                    overlap_size += ol_len
                current_chunk = overlap_lines.copy()
                current_size = overlap_size

            current_chunk.append(line)
            current_size += line_len

        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "file_path": filepath,
                "category": self.get_file_category(filepath),
                "chunk_id": str(uuid.uuid4()),
                "chunk_number": len(chunks) + 1,
            })

        return chunks

    def process_repository(self) -> List[Dict]:
        if not self.repo_path.exists():
            raise FileNotFoundError(
                f"Repository '{self.repo_name}' not found at {self.repo_path}"
            )

        chunks = []
        for path in self.walk_repository():
            content = self.read_file_safe(path)
            if content is None:
                continue
            chunks.extend(self.chunk_document(content, str(path)))

        return chunks


class RepositoryIndexer:
    def __init__(self, repo_name: str):
        self.repo_name = repo_name

    @staticmethod
    def generate_embeddings(texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        texts = [t for t in texts if t is not None]
        if not texts:
            return []
        try:
            response = ollama.embed(model=EMBEDDING_MODEL, input=texts)
            return response["embeddings"]
        except Exception as e:
            raise RuntimeError(
                f"Ollama embedding failed for model '{EMBEDDING_MODEL}': {e}"
            ) from e

    @staticmethod
    def get_chromadb_client():
        CHROMADB_PATH.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=str(CHROMADB_PATH),
            settings=Settings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self):
        client = self.get_chromadb_client()
        return client.get_or_create_collection(
            name=self.repo_name,
            metadata={"repo_name": self.repo_name},
        )
