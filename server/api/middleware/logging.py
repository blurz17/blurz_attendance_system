"""
Request logging middleware — logs method, path, status, duration for each request.
Pure ASGI middleware (not BaseHTTPMiddleware).
"""
import time
import logging

logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware:
    """Logs every HTTP request with status code and duration."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        method = scope.get("method", "?")
        path = scope.get("path", "/")
        query = scope.get("query_string", b"").decode("utf-8")
        full_path = f"{path}?{query}" if query else path

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        status_holder = [0]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            ms = (time.time() - start) * 1000
            code = status_holder[0]
            level = "ERROR" if code >= 500 else "WARN" if code >= 400 else "INFO"
            logger.info(f"{level} {code} {method:<7} {full_path:<40} | {ms:7.1f}ms | IP: {client_ip}")

        except Exception as e:
            ms = (time.time() - start) * 1000
            logger.error(f"ERROR 500 {method:<7} {path:<40} | {ms:7.1f}ms | IP: {client_ip} | {type(e).__name__}: {e}")
            raise
