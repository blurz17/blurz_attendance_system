"""
Rate limiting middleware — Redis-based per-user/IP rate limiter.

Implemented as a raw ASGI middleware (not BaseHTTPMiddleware) to avoid
anyio task-group conflicts with pytest-asyncio on Windows.
"""
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

from core.db.redis import token_blacklist as redis_client

RATE_LIMIT_REQUESTS = 60       # Max requests per window
RATE_LIMIT_WINDOW = 60         # Window size in seconds
RATE_LIMIT_PREFIX = "rate_limit:"

SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)

        # Skip rate limiting for docs / health
        if request.url.path in SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        key = self._get_rate_limit_key(request, scope)

        try:
            current = await redis_client.incr(f"{RATE_LIMIT_PREFIX}{key}")

            if current == 1:
                await redis_client.expire(f"{RATE_LIMIT_PREFIX}{key}", RATE_LIMIT_WINDOW)

            if current > RATE_LIMIT_REQUESTS:
                ttl = await redis_client.ttl(f"{RATE_LIMIT_PREFIX}{key}")
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "retry_after": ttl},
                    headers={"Retry-After": str(ttl)},
                )
                await response(scope, receive, send)
                return

        except Exception as e:
            logging.warning(f"Rate limiter error (allowing request): {e}")
            await self.app(scope, receive, send)
            return

        # Wrap send to inject rate-limit headers
        remaining = max(0, RATE_LIMIT_REQUESTS - current)
        headers_to_add = {
            b"x-ratelimit-limit": str(RATE_LIMIT_REQUESTS).encode(),
            b"x-ratelimit-remaining": str(remaining).encode(),
        }

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for k, v in headers_to_add.items():
                    headers.append((k, v))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _get_rate_limit_key(self, request: Request, scope: Scope) -> str:
        """Generate rate limit key — per-user if authenticated, per-IP otherwise."""
        user = scope.get("state", {}).get("user")
        if user and isinstance(user, dict) and user.get("id"):
            return f"user:{user['id']}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
