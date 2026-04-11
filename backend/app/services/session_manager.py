import logging

from sqlalchemy import asc

from app.db import SessionLocal
from app.models import ConversationTurn

logger = logging.getLogger(__name__)

MAX_HISTORY_TOKENS = 4000


class SessionManager:
    def get_history(self, session_id: str, max_turns: int = 10) -> list[dict]:
        session = SessionLocal()
        try:
            rows = (
                session.query(ConversationTurn)
                .filter(ConversationTurn.session_id == session_id)
                .order_by(asc(ConversationTurn.created_at))
                .limit(max_turns)
                .all()
            )
            history = [{"role": r.role, "content": r.content} for r in rows]
            return self.truncate_by_tokens(history, MAX_HISTORY_TOKENS)
        finally:
            session.close()

    def save_turn(self, session_id: str, role: str, content: str) -> None:
        session = SessionLocal()
        try:
            session.add(ConversationTurn(
                session_id=session_id, role=role, content=content,
            ))
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("save_turn failed session=%s role=%s", session_id, role)
        finally:
            session.close()

    @staticmethod
    def truncate_by_tokens(history: list[dict], max_tokens: int = MAX_HISTORY_TOKENS) -> list[dict]:
        total = sum(len(h["content"]) // 2 for h in history)
        while history and total > max_tokens:
            removed = history.pop(0)
            total -= len(removed["content"]) // 2
        return history
