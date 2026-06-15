import logging
from fastapi import APIRouter, HTTPException, status
from app.models.rag import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    RetrievalResult,
    CollectionsListResponse,
    CollectionInfo,
    QARequest,
    QAResponse,
    SourceSummary,
    RepositorySummaryRequest,
    RepositorySummaryResponse,
)
from app.services.rag_service import RepositoryIndexer, RAGRetriever
from app.services.repository_qa import RepositoryQA
from app.services.repository_summary import RepositorySummary

logger = logging.getLogger(__name__)
rag_router = APIRouter(prefix="/rag", tags=["RAG - Repository Search"])


@rag_router.post("/index-repository", response_model=IndexResponse)
async def index_repository(request: IndexRequest):
    if not RepositoryIndexer.repository_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' not found",
        )

    try:
        logger.info("Indexing repository '%s' started", request.repo_name)
        indexer = RepositoryIndexer(request.repo_name)
        result = indexer.index_repository()
        logger.info("Indexing repository '%s' completed", request.repo_name)
        return IndexResponse(
            status=result["status"],
            repo_name=result["repo_name"],
            documents=result["documents"],
            collection=result["collection"],
        )
    except Exception as e:
        logger.error("Indexing repository '%s' failed: %s", request.repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index repository: {e}",
        )


@rag_router.post("/ask-repository", response_model=QueryResponse)
async def ask_repository(request: QueryRequest):
    if not RepositoryIndexer.repository_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' not found",
        )

    if not RAGRetriever.collection_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' has not been indexed",
        )

    try:
        logger.info("Retrieval request for '%s': query='%s'", request.repo_name, request.query)
        results = RAGRetriever.retrieve(request.repo_name, request.query, request.top_k)
    except Exception as e:
        logger.error("Retrieval failed for '%s': %s", request.repo_name, e)
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
        logger.info("Listed %s collections", len(collections))
    except Exception as e:
        logger.error("Failed to list collections: %s", e)
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


@rag_router.post("/qa", response_model=QAResponse)
async def repository_qa(request: QARequest):
    if not RepositoryIndexer.repository_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' not found",
        )

    if not RAGRetriever.collection_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' has not been indexed",
        )

    try:
        logger.info("QA request for '%s': query='%s'", request.repo_name, request.query)
        qa = RepositoryQA()
        result = qa.generate_answer(request.repo_name, request.query, request.top_k)
    except RuntimeError as e:
        if "LLM" in str(e):
            logger.error("QA LLM error for '%s': %s", request.repo_name, e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service unavailable",
            )
        logger.error("QA runtime error for '%s': %s", request.repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error("QA failed for '%s': %s", request.repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QA generation failed: {e}",
        )

    sources = [
        RetrievalResult(
            content=r["content"],
            file_path=r["file_path"],
            category=r["category"],
            chunk_id=r["chunk_id"],
            chunk_number=r["chunk_number"],
            relevance_score=r["relevance_score"],
        )
        for r in result["sources"]
    ]

    source_summary = [
        SourceSummary(
            file_path=r["file_path"],
            category=r["category"],
            relevance_score=r["relevance_score"],
        )
        for r in result["sources"]
    ]

    return QAResponse(
        repo_name=request.repo_name,
        query=request.query,
        answer=result["answer"],
        sources=sources,
        source_summary=source_summary,
    )


@rag_router.post("/repository-summary", response_model=RepositorySummaryResponse)
async def repository_summary(request: RepositorySummaryRequest):
    if not RepositoryIndexer.repository_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' not found",
        )

    if not RAGRetriever.collection_exists(request.repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_name}' has not been indexed",
        )

    try:
        logger.info("Summary request for '%s'", request.repo_name)
        summarizer = RepositorySummary(request.repo_name)
        result = summarizer.generate_summary()
    except RuntimeError as e:
        if "LLM" in str(e):
            logger.error("Summary LLM error for '%s': %s", request.repo_name, e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service unavailable",
            )
        logger.error("Summary runtime error for '%s': %s", request.repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Summary failed for '%s': %s", request.repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository summary failed: {e}",
        )

    return RepositorySummaryResponse(
        repo_name=request.repo_name,
        summary=result["summary"],
        architecture=result["architecture"],
        technologies=result["technologies"],
        sources=result["sources"],
    )


@rag_router.delete("/collection/{repo_name}")
async def delete_collection(repo_name: str):
    if not RepositoryIndexer.repository_exists(repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_name}' not found",
        )

    if not RAGRetriever.collection_exists(repo_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_name}' has not been indexed",
        )

    try:
        logger.info("Deleting collection for '%s'", repo_name)
        indexer = RepositoryIndexer(repo_name)
        indexer.delete_collection()
        logger.info("Collection deleted for '%s'", repo_name)
        return {
            "status": "deleted",
            "repo_name": repo_name,
            "message": f"Successfully deleted index for {repo_name}",
        }
    except Exception as e:
        logger.error("Failed to delete collection for '%s': %s", repo_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {e}",
        )
