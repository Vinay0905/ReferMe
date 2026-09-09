import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("referme.http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Intercepts all incoming HTTP requests to log methods, paths, status codes, and execution latencies with unique Request-IDs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Resolve or generate request identifier
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req:{uuid.uuid4().hex[:8]}"

        request.state.request_id = request_id

        # Determine client address
        client_host = request.client.host if request.client else "unknown"
        query_str = f"?{request.url.query}" if request.url.query else ""
        path = request.url.path

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

            status = response.status_code
            log_msg = f"[{request_id}] {request.method} {path}{query_str} -> {status} ({duration_ms:.1f}ms) | IP: {client_host}"

            if status >= 500:
                logger.error(log_msg)
            elif status >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {path}{query_str} -> EXCEPTION ({duration_ms:.1f}ms) | IP: {client_host} | Error: {exc}",
                exc_info=True,
            )
            raise exc
