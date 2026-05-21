from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TrackingMiddleware(BaseHTTPMiddleware):
    """Extract client IP from request and inject into request.state."""

    async def dispatch(self, request: Request, call_next):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            request.state.client_ip = forwarded.split(",")[0].strip()
        else:
            request.state.client_ip = request.client.host if request.client else None
        response = await call_next(request)
        return response
