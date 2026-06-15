from app.services.rag_service import RAGRetriever
from app.services.ollama_service import ask_llm


class RepositoryQA:
    def __init__(self):
        self.retriever = RAGRetriever()

    def generate_answer(self, repo_name: str, query: str, top_k: int = 5) -> dict:
        chunks = self.retriever.retrieve(repo_name, query, top_k)

        if not chunks:
            return {
                "answer": "No relevant information found in the repository.",
                "sources": [],
            }

        prompt = self._build_prompt(chunks, query)
        system = (
            "You are a codebase assistant. Answer the user's question "
            "using only the provided context. If the context does not "
            "contain enough information, say so. Do not invent information."
        )

        answer = ask_llm(prompt, system=system)

        return {"answer": answer, "sources": chunks}

    def _build_prompt(self, chunks: list, query: str) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[Source {i + 1}]\n"
                f"File: {chunk['file_path']}\n"
                f"Relevance: {chunk['relevance_score']}\n"
                f"Content:\n{chunk['content']}\n"
            )

        context = "\n---\n".join(context_parts)

        prompt = (
            f"Context from the repository:\n\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer based on the context above."
        )
        return prompt
