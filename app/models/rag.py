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


class SourceSummary(BaseModel):
    file_path: str
    category: str
    relevance_score: float


class QARequest(BaseModel):
    repo_name: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class QAResponse(BaseModel):
    repo_name: str
    query: str
    answer: str
    sources: List[RetrievalResult]
    source_summary: List[SourceSummary]


class RepositorySummaryRequest(BaseModel):
    repo_name: str


class RepositorySummaryResponse(BaseModel):
    repo_name: str
    summary: str
    architecture: str
    technologies: List[str]
    sources: List[str]


class CollectionsListResponse(BaseModel):
    collections: List[CollectionInfo]
    total: int
