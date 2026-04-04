from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    source_name: str
    content: str
    score: float


class VectorStore:
    def hybrid_search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        # MVP 占位：后续替换为 BM25 + pgvector 检索 + rerank
        mock = [
            RetrievedChunk(
                source_name="profile.md",
                content="候选人具备 RAG 全栈开发经验，覆盖前后端与向量检索链路。",
                score=0.92,
            ),
            RetrievedChunk(
                source_name="faq.md",
                content="擅长 FastAPI、React、PostgreSQL 与检索优化。",
                score=0.88,
            ),
        ]
        return mock[:top_k]
