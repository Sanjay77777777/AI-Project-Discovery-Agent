import logging
from app.services.rag_service import RAGRetriever
from app.services.ollama_service import ask_llm
from app.config import MAX_CONTEXT_CHUNKS

logger = logging.getLogger(__name__)


class RepositoryQA:
    def __init__(self):
        self.retriever = RAGRetriever()

    def generate_answer(self, repo_name: str, query: str, top_k: int = MAX_CONTEXT_CHUNKS) -> dict:
        logger.info("QA request for '%s': query='%s', top_k=%s", repo_name, query, top_k)
        chunks = self.retriever.retrieve(repo_name, query, top_k)

        if not chunks:
            logger.info("QA for '%s': no chunks retrieved, skipping LLM", repo_name)
            return {
                "answer": "I could not find enough information in the repository context.",
                "sources": [],
                "source_summary": [],
            }

        prompt = self._build_prompt(chunks, query)
        system = (
            "You are a repository QA assistant.\n\n"
            "Answer ONLY using the provided repository context.\n\n"
            "If the answer cannot be found in the context, respond:\n"
            "'I could not find enough information in the repository context.'\n\n"
            "Do not use external knowledge.\n"
            "Do not guess.\n"
            "Do not invent APIs, functions, files, or behaviors."
        )

        answer = ask_llm(prompt, system=system)

        source_summary = [
            {
                "file_path": c["file_path"],
                "category": c["category"],
                "relevance_score": c["relevance_score"],
            }
            for c in chunks
        ]

        return {"answer": answer, "sources": chunks, "source_summary": source_summary}

    def _build_prompt(self, chunks: list, query: str) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"<<< SOURCE {i + 1} >>>\n"
                f"File:     {chunk['file_path']}\n"
                f"Category: {chunk['category']}\n"
                f"Score:    {chunk['relevance_score']}\n"
                f"Content:\n{chunk['content']}\n"
            )

        context = "\n==========\n".join(context_parts)

        prompt = (
            f"Repository Context:\n\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer based solely on the context above."
        )
        return prompt
