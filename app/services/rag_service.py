import logging
from pathlib import Path
import os
import uuid
from typing import Generator, List, Dict, Optional, Any

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

logger = logging.getLogger(__name__)


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
            logger.warning("Repository path not found: %s", self.repo_path)
            raise FileNotFoundError(
                f"Repository '{self.repo_name}' not found"
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
    def repository_exists(repo_name: str) -> bool:
        return (REPOSITORIES_DIR / repo_name).exists()

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
            metadata={"repo_name": self.repo_name, "hnsw:space": "cosine"},
        )

    def store_documents(self, collection, chunks: List[Dict]):
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            documents.append(chunk["content"])
            metadatas.append({
                "file_path": chunk["file_path"],
                "category": chunk["category"],
                "chunk_number": str(chunk["chunk_number"]),
            })
            ids.append(chunk["chunk_id"])

        embeddings = self.generate_embeddings(documents)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def delete_collection(self):
        try:
            client = self.get_chromadb_client()
            client.delete_collection(self.repo_name)
        except Exception:
            pass

    def index_repository(self) -> Dict:
        repo_path = REPOSITORIES_DIR / self.repo_name
        if not repo_path.exists():
            logger.warning("Repository path not found: %s", repo_path)
            raise FileNotFoundError(
                f"Repository '{self.repo_name}' not found"
            )

        logger.info("Indexing repository '%s' started", self.repo_name)
        processor = DocumentProcessor(self.repo_name)
        chunks = processor.process_repository()

        self.delete_collection()
        collection = self.get_or_create_collection()

        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch_num = i // batch_size + 1
            logger.info("Indexing batch %s/%s for '%s'", batch_num, total_batches, self.repo_name)
            batch = chunks[i:i + batch_size]
            self.store_documents(collection, batch)

        logger.info("Indexing repository '%s' completed: %s chunks", self.repo_name, len(chunks))
        return {
            "status": "indexed",
            "repo_name": self.repo_name,
            "documents": len(chunks),
            "collection": self.repo_name,
        }


class RAGRetriever:
    @staticmethod
    def collection_exists(repo_name: str) -> bool:
        try:
            client = RepositoryIndexer.get_chromadb_client()
            client.get_collection(repo_name)
            return True
        except Exception:
            return False

    @staticmethod
    def retrieve(
        repo_name: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        logger.info("Retrieval request for '%s': query='%s', top_k=%s", repo_name, query, top_k)
        client = RepositoryIndexer.get_chromadb_client()
        collection = client.get_collection(repo_name)

        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query)
        query_embedding = response["embedding"]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        retrieved = []
        if not results["ids"] or not results["ids"][0]:
            logger.info("Retrieval for '%s' returned 0 chunks", repo_name)
            return retrieved

        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i] if results.get("distances") else 0.0
            relevance_score = max(
                0.0, min(1.0, 1.0 - (distance / 2.0))
            )
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

            retrieved.append({
                "content": results["documents"][0][i],
                "file_path": metadata.get("file_path", ""),
                "category": metadata.get("category", "code"),
                "chunk_id": results["ids"][0][i],
                "chunk_number": int(metadata.get("chunk_number", 0)),
                "relevance_score": round(relevance_score, 4),
            })

        retrieved.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info("Retrieval for '%s' returned %s chunks", repo_name, len(retrieved))
        return retrieved
