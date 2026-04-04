from app.schemas import Citation
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore


class RAGService:
    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()

    def answer(self, question: str) -> tuple[str, list[Citation]]:
        retrieved = self.vector_store.hybrid_search(question, top_k=5)
        context_blocks = [item.content for item in retrieved]
        answer = self.llm_client.generate_answer(question, context_blocks)

        citations = [
            Citation(source_name=item.source_name, snippet=item.content)
            for item in retrieved[:3]
        ]
        return answer, citations
