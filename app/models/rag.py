from pydantic import BaseModel, Field
from typing import Optional, List


class IndexRequest(BaseModel):
    repo_name: str = Field(..., description="Name of the repository to index")


class IndexResponse(BaseModel):
    status: str
    repo_name: str
    documents: int
    collection: str
    message: Optional[str] = None


class QueryRequest(BaseModel):
    repo_name: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalResult(BaseModel):
    content: str
    file_path: str
    category: str
    chunk_id: str
    chunk_number: int
    relevance_score: float


class QueryResponse(BaseModel):
    repo_name: str
    query: str
    results: List[RetrievalResult]
    count: int


class CollectionInfo(BaseModel):
    repo_name: str
    exists: bool
    document_count: int
    metadata: dict = {}


class CollectionsListResponse(BaseModel):
    collections: List[CollectionInfo]
    total: int
