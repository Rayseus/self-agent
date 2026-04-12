import logging
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import SessionLocal
from app.models import QALog
from app.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
rag_service = RAGService()
session_manager = SessionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _save_qa_log(
    question: str,
    answer: str,
    trace_id: str,
    latency_ms: float,
    hit_chunks: list[dict],
    retrieval_scores: list[float],
) -> None:
    session = SessionLocal()
    try:
        session.add(
            QALog(
                question=question,
                answer=answer,
                trace_id=trace_id,
                latency_ms=latency_ms,
                hit_chunks=hit_chunks,
                retrieval_scores=retrieval_scores,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("qa_log write failed trace=%s", trace_id)
    finally:
        session.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, bg: BackgroundTasks) -> ChatResponse:
    trace_id = str(uuid4())
    history = session_manager.get_history(req.session_id)
    result = rag_service.answer(req.question, history=history)
    logger.info(
        "trace=%s session=%s latency=%.1fms citations=%d history_turns=%d",
        trace_id, req.session_id, result.latency_ms, len(result.citations), len(history),
    )
    bg.add_task(session_manager.save_turn, req.session_id, "user", req.question)
    bg.add_task(session_manager.save_turn, req.session_id, "assistant", result.answer)
    bg.add_task(
        _save_qa_log,
        question=req.question,
        answer=result.answer,
        trace_id=trace_id,
        latency_ms=result.latency_ms,
        hit_chunks=result.hit_chunks,
        retrieval_scores=result.retrieval_scores,
    )
    return ChatResponse(answer=result.answer, citations=result.citations, trace_id=trace_id)
