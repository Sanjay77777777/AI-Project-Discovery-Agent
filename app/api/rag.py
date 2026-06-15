from fastapi import APIRouter, HTTPException, status
from app.models.rag import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    RetrievalResult,
    CollectionsListResponse,
    CollectionInfo,
)
from app.services.rag_service import RepositoryIndexer, RAGRetriever

rag_router = APIRouter(prefix="/rag", tags=["RAG - Repository Search"])


@rag_router.post("/index-repository", response_model=IndexResponse)
async def index_repository(request: IndexRequest):
    try:
        indexer = RepositoryIndexer(request.repo_name)
        result = indexer.index_repository()
        return IndexResponse(
            status=result["status"],
            repo_name=result["repo_name"],
            documents=result["documents"],
            collection=result["collection"],
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index repository: {e}",
        )


@rag_router.post("/ask-repository", response_model=QueryResponse)
async def ask_repository(request: QueryRequest):
    if not RAGRetriever.collection_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' not indexed.",
        )

    try:
        results = RAGRetriever.retrieve(request.repo_name, request.query, request.top_k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query repository: {e}",
        )

    retrieval_results = [
        RetrievalResult(
            content=r["content"],
            file_path=r["file_path"],
            category=r["category"],
            chunk_id=r["chunk_id"],
            chunk_number=r["chunk_number"],
            relevance_score=r["relevance_score"],
        )
        for r in results
    ]

    return QueryResponse(
        repo_name=request.repo_name,
        query=request.query,
        results=retrieval_results,
        count=len(retrieval_results),
    )


@rag_router.get("/collections", response_model=CollectionsListResponse)
async def list_collections():
    try:
        client = RepositoryIndexer.get_chromadb_client()
        collections = client.list_collections()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {e}",
        )

    collection_info = []
    for c in collections:
        collection_info.append(
            CollectionInfo(
                repo_name=c.name,
                exists=True,
                document_count=c.count(),
                metadata=c.metadata or {},
            )
        )

    return CollectionsListResponse(
        collections=collection_info,
        total=len(collection_info),
    )


@rag_router.delete("/collection/{repo_name}")
async def delete_collection(repo_name: str):
    try:
        indexer = RepositoryIndexer(repo_name)
        indexer.delete_collection()
        return {
            "status": "deleted",
            "repo_name": repo_name,
            "message": f"Successfully deleted index for {repo_name}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {e}",
        )
