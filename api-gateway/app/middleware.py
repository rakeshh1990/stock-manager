import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("gateway.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with:
      - trace_id  : unique per-request UUID (useful when you add Loki later)
      - method    : HTTP verb
      - path      : URL path
      - status    : response status code
      - duration  : wall-clock ms
      - user_id   : extracted from X-User-Id header if present (set by deps.py)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        user_id = request.headers.get("X-User-Id", "-")

        logger.info(
            "request",
            extra={
                "trace_id":  trace_id,
                "method":    request.method,
                "path":      request.url.path,
                "status":    response.status_code,
                "duration":  duration_ms,
                "user_id":   user_id,
            },
        )
        # Propagate trace_id back to client for debugging
        response.headers["X-Trace-Id"] = trace_id
        return response