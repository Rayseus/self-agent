from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import APIKeyHeader

from app.config import settings
from app.services import analytics_service

router = APIRouter(prefix="/admin", tags=["admin"])

_header_scheme = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def _verify_token(token: str | None = Depends(_header_scheme)) -> None:
    if not settings.admin_token:
        raise HTTPException(503, "Admin token not configured")
    if token != settings.admin_token:
        raise HTTPException(401, "Unauthorized")


@router.get("/stats")
def stats(
    from_date: date = Query(None, alias="from"),
    to_date: date = Query(None, alias="to"),
    _: None = Depends(_verify_token),
):
    if not from_date:
        from_date = date.today() - timedelta(days=7)
    if not to_date:
        to_date = date.today()
    return analytics_service.get_stats(from_date, to_date)


@router.get("/questions")
def questions(
    day: date = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: None = Depends(_verify_token),
):
    if not day:
        day = date.today()
    return analytics_service.list_questions(day, limit, offset)


@router.post("/aggregate")
def aggregate(
    day: date = Query(None),
    _: None = Depends(_verify_token),
):
    if not day:
        day = date.today() - timedelta(days=1)
    result = analytics_service.aggregate_daily(day)
    return result
