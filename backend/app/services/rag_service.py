import time
from dataclasses import dataclass, field

from app.schemas import Citation
from app.services.llm_client import REFUSE_ANSWER, LLMClient
from app.services.vector_store import VectorStore

MIN_RRF_SCORE = 0.005


@dataclass
class AnswerResult:
    answer: str
    citations: list[Citation]
    latency_ms: float
    hit_chunks: list[dict] = field(default_factory=list)
    retrieval_scores: list[float] = field(default_factory=list)


class RAGService:
    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()

    def answer(self, question: str) -> AnswerResult:
        t0 = time.perf_counter()

        retrieved = self.vector_store.hybrid_search(question, top_k=5)
        relevant = [r for r in retrieved if r.score >= MIN_RRF_SCORE]

        hit_chunks = [
            {"source": r.source_name, "snippet": r.content[:200]} for r in relevant
        ]
        retrieval_scores = [r.score for r in relevant]

        if not relevant:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            return AnswerResult(REFUSE_ANSWER, [], latency)

        numbered_lines = [
            f"[{i}] From: {item.source_name}\n{item.content}"
            for i, item in enumerate(relevant, 1)
        ]
        numbered_context = "\n\n".join(numbered_lines)

        answer = self.llm_client.generate_answer(question, numbered_context)

        if answer == REFUSE_ANSWER:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            return AnswerResult(REFUSE_ANSWER, [], latency, hit_chunks, retrieval_scores)

        citations = [
            Citation(source_name=item.source_name, snippet=item.content[:200])
            for item in relevant
        ]

        latency = round((time.perf_counter() - t0) * 1000, 1)
        return AnswerResult(answer, citations, latency, hit_chunks, retrieval_scores)
