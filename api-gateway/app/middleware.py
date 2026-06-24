import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("gateway.access")

# Paths that return streaming responses (SSE).
# BaseHTTPMiddleware buffers responses before returning them, which
# completely breaks SSE — the client never receives any events.
# We detect these paths and skip logging middleware entirely,
# letting the response pass through the ASGI stack unmodified.
SSE_PATHS = {"/scan/stream"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass middleware for SSE endpoints — do NOT buffer streaming responses
        if request.url.path in SSE_PATHS:
            return await call_next(request)

        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        user_id = request.headers.get("X-User-Id", "-")

        logger.info(
            "request",
            extra={
                "trace_id": trace_id,
                "method":   request.method,
                "path":     request.url.path,
                "status":   response.status_code,
                "duration": duration_ms,
                "user_id":  user_id,
            },
        )
        response.headers["X-Trace-Id"] = trace_id
        return response