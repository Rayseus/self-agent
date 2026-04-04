import re
from dataclasses import dataclass

from sqlalchemy import text

from app.db import SessionLocal
from app.services.embedding_client import embed_query


@dataclass
class RetrievedChunk:
    source_name: str
    content: str
    score: float


def _extract_keywords(query: str) -> list[str]:
    """从查询中提取中文词和英文单词作为关键词。"""
    cjk_chars = re.findall(r"[\u4e00-\u9fff]{2,}", query)
    ascii_words = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", query)
    return cjk_chars + [w.lower() for w in ascii_words]


class VectorStore:
    def hybrid_search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        vec_results = self._vector_search(query, top_k=top_k * 2)
        kw_results = self._keyword_search(query, top_k=top_k * 2)
        merged = self._rrf_merge(vec_results, kw_results, top_k=top_k)
        return merged

    def _vector_search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        query_vec = embed_query(query)
        session = SessionLocal()
        try:
            rows = session.execute(
                text("""
                    SELECT c.chunk_text, c.metadata->>'source' AS source_name,
                           1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
                    FROM embeddings e
                    JOIN chunks c ON c.id = e.chunk_id
                    ORDER BY e.embedding <=> CAST(:qvec AS vector)
                    LIMIT :lim
                """),
                {"qvec": str(query_vec), "lim": top_k},
            ).fetchall()
            return [
                RetrievedChunk(
                    source_name=r.source_name or "",
                    content=r.chunk_text,
                    score=float(r.score),
                )
                for r in rows
            ]
        finally:
            session.close()

    def _keyword_search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        keywords = _extract_keywords(query)
        if not keywords:
            return []

        like_clauses = " + ".join(
            [f"(CASE WHEN c.chunk_text ILIKE :kw{i} THEN 1 ELSE 0 END)" for i in range(len(keywords))]
        )
        sql = f"""
            SELECT c.chunk_text, c.metadata->>'source' AS source_name,
                   ({like_clauses})::float / :total AS score
            FROM chunks c
            WHERE {" OR ".join([f"c.chunk_text ILIKE :kw{i}" for i in range(len(keywords))])}
            ORDER BY score DESC
            LIMIT :lim
        """
        params: dict = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
        params["total"] = len(keywords)
        params["lim"] = top_k

        session = SessionLocal()
        try:
            rows = session.execute(text(sql), params).fetchall()
            return [
                RetrievedChunk(
                    source_name=r.source_name or "",
                    content=r.chunk_text,
                    score=float(r.score),
                )
                for r in rows
            ]
        finally:
            session.close()

    @staticmethod
    def _rrf_merge(
        vec_results: list[RetrievedChunk],
        kw_results: list[RetrievedChunk],
        top_k: int = 5,
        k: int = 60,
    ) -> list[RetrievedChunk]:
        """Reciprocal Rank Fusion 合并两路检索结果。"""
        score_map: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        for rank, item in enumerate(vec_results):
            key = item.content
            score_map[key] = score_map.get(key, 0) + 1.0 / (k + rank + 1)
            chunk_map[key] = item

        for rank, item in enumerate(kw_results):
            key = item.content
            score_map[key] = score_map.get(key, 0) + 1.0 / (k + rank + 1)
            chunk_map[key] = item

        sorted_keys = sorted(score_map, key=lambda x: score_map[x], reverse=True)[:top_k]
        return [
            RetrievedChunk(
                source_name=chunk_map[k_].source_name,
                content=chunk_map[k_].content,
                score=round(score_map[k_], 6),
            )
            for k_ in sorted_keys
        ]
