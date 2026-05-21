import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.admin import router as admin_router
from app.config import settings
from app.db import SessionLocal
from app.middleware.tracking import TrackingMiddleware
from app.models import QALog
from app.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ingest 默认由 GitHub Actions 在 data/** 变更时远程触发（见 .github/workflows/ingest.yml），
    # 服务启动时不再阻塞跑 ingest。仅在显式设置 INGEST_ON_BOOT=1 时作为应急后门触发一次。
    if os.environ.get("INGEST_ON_BOOT") == "1":
        logger.info("knowledge ingest: starting (INGEST_ON_BOOT=1)")
        try:
            from scripts.ingest import ingest

            ingest()
            logger.info("knowledge ingest: done")
        except Exception:
            logger.exception("knowledge ingest failed; service will still start")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
rag_service = RAGService()
session_manager = SessionManager()

app.add_middleware(TrackingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_router)


def _save_qa_log(
    question: str,
    answer: str,
    trace_id: str,
    latency_ms: float,
    hit_chunks: list[dict],
    retrieval_scores: list[float],
    session_id: str | None = None,
    client_ip: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            QALog(
                question=question,
                answer=answer,
                trace_id=trace_id,
                latency_ms=latency_ms,
                hit_chunks=hit_chunks,
                retrieval_scores=retrieval_scores,
                session_id=session_id,
                client_ip=client_ip,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("qa_log write failed trace=%s", trace_id)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request, bg: BackgroundTasks) -> ChatResponse:
    trace_id = str(uuid4())
    client_ip = getattr(request.state, "client_ip", None)
    history = session_manager.get_history(req.session_id)
    result = rag_service.answer(req.question, history=history)
    logger.info(
        "trace=%s session=%s ip=%s latency=%.1fms citations=%d history_turns=%d",
        trace_id, req.session_id, client_ip, result.latency_ms, len(result.citations), len(history),
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
        session_id=req.session_id,
        client_ip=client_ip,
    )
    return ChatResponse(answer=result.answer, citations=result.citations, trace_id=trace_id)
