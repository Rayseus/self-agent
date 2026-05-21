import logging
from collections import Counter
from datetime import date

from sqlalchemy import text

from app.db import SessionLocal

logger = logging.getLogger(__name__)


def aggregate_daily(day: date) -> dict:
    """Aggregate qa_logs for a given day into qa_daily_summary. Idempotent."""
    session = SessionLocal()
    try:
        row = session.execute(
            text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(DISTINCT session_id) AS sessions,
                    COUNT(DISTINCT client_ip) AS ips,
                    AVG(latency_ms) AS avg_lat
                FROM qa_logs
                WHERE created_at::date = :day
            """),
            {"day": day},
        ).fetchone()

        total = row[0] or 0
        sessions = row[1] or 0
        ips = row[2] or 0
        avg_lat = round(row[3], 1) if row[3] else None

        questions = session.execute(
            text("""
                SELECT question FROM qa_logs
                WHERE created_at::date = :day
            """),
            {"day": day},
        ).fetchall()

        counter = Counter(q[0].strip().lower() for q in questions)
        top = [{"question": q, "count": c} for q, c in counter.most_common(10)]

        session.execute(
            text("""
                INSERT INTO qa_daily_summary (day, total_questions, unique_sessions, unique_ips, avg_latency_ms, top_questions, generated_at)
                VALUES (:day, :total, :sessions, :ips, :avg_lat, :top::jsonb, NOW())
                ON CONFLICT (day) DO UPDATE SET
                    total_questions = EXCLUDED.total_questions,
                    unique_sessions = EXCLUDED.unique_sessions,
                    unique_ips = EXCLUDED.unique_ips,
                    avg_latency_ms = EXCLUDED.avg_latency_ms,
                    top_questions = EXCLUDED.top_questions,
                    generated_at = NOW()
            """),
            {"day": day, "total": total, "sessions": sessions, "ips": ips, "avg_lat": avg_lat, "top": __import__("json").dumps(top, ensure_ascii=False)},
        )
        session.commit()
        return {"day": str(day), "total_questions": total, "unique_sessions": sessions, "unique_ips": ips, "avg_latency_ms": avg_lat, "top_questions": top}
    except Exception:
        session.rollback()
        logger.exception("aggregate_daily failed for day=%s", day)
        raise
    finally:
        session.close()


def get_stats(from_date: date, to_date: date) -> dict:
    """Return aggregated stats for a date range."""
    session = SessionLocal()
    try:
        row = session.execute(
            text("""
                SELECT
                    COALESCE(SUM(total_questions), 0),
                    COALESCE(SUM(unique_sessions), 0),
                    COALESCE(SUM(unique_ips), 0),
                    AVG(avg_latency_ms)
                FROM qa_daily_summary
                WHERE day BETWEEN :from_date AND :to_date
            """),
            {"from_date": from_date, "to_date": to_date},
        ).fetchone()

        days = session.execute(
            text("""
                SELECT COUNT(*) FROM qa_daily_summary
                WHERE day BETWEEN :from_date AND :to_date AND total_questions > 0
            """),
            {"from_date": from_date, "to_date": to_date},
        ).scalar()

        return {
            "from": str(from_date),
            "to": str(to_date),
            "total_questions": row[0],
            "unique_sessions": row[1],
            "unique_ips": row[2],
            "avg_latency_ms": round(row[3], 1) if row[3] else None,
            "active_days": days or 0,
        }
    finally:
        session.close()


def list_questions(day: date, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return questions for a given day, ordered by time desc."""
    session = SessionLocal()
    try:
        rows = session.execute(
            text("""
                SELECT question, trace_id, session_id, client_ip, created_at
                FROM qa_logs
                WHERE created_at::date = :day
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"day": day, "limit": limit, "offset": offset},
        ).fetchall()
        return [
            {
                "question": r[0],
                "trace_id": r[1],
                "session_id": r[2],
                "client_ip": str(r[3]) if r[3] else None,
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    finally:
        session.close()
