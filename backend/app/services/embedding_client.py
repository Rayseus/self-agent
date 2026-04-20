import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class EmbeddingError(RuntimeError):
    """Embedding 调用失败。由上层决定是否降级（检索层降级为空召回 → 拒答）。"""


def _request(payload: dict, model: str | None = None) -> dict:
    model = model or settings.embedding_model
    url = f"{GEMINI_BASE}/{model}:embedContent?key={settings.gemini_api_key}"
    proxy = settings.proxy_url or None
    try:
        with httpx.Client(proxy=proxy, timeout=30) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Gemini embedding HTTP error: %s — %s", e.response.status_code, e.response.text[:500])
        raise EmbeddingError(f"http {e.response.status_code}") from e
    except (httpx.TimeoutException, httpx.TransportError) as e:
        logger.error("Gemini embedding transport failure: %s", e)
        raise EmbeddingError("transport failure") from e
    except Exception as e:
        logger.exception("Gemini embedding unexpected error")
        raise EmbeddingError("unexpected") from e


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """批量生成 Embedding（逐条调用，Gemini embedContent 仅支持单条）。"""
    vectors: list[list[float]] = []
    for t in texts:
        data = _request({
            "model": settings.embedding_model,
            "content": {"parts": [{"text": t}]},
            "taskType": task_type,
        })
        vectors.append(data["embedding"]["values"])
    return vectors


def embed_query(text: str) -> list[float]:
    """为检索查询生成 Embedding。失败时抛 EmbeddingError，由调用方降级处理。"""
    data = _request({
        "model": settings.embedding_model,
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_QUERY",
    })
    return data["embedding"]["values"]
