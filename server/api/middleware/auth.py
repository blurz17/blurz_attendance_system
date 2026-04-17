"""
Auth middleware — JWT verification for protected routes.
Attaches decoded user data to request.state.user.

Implemented as a raw ASGI middleware (not BaseHTTPMiddleware) to avoid
anyio task-group conflicts with pytest-asyncio on Windows.
"""
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

from core.security import decode_token
from core.db.redis import check_blacklist

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/verify",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/password-reset",
    "/api/v1/auth/confirm-password",
    "/api/v1/admin/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
]


class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        path = request.url.path

        # Skip public paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            await self.app(scope, receive, send)
            return

        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Soft check — route-level Depends() will enforce auth
            await self.app(scope, receive, send)
            return

        token_str = auth_header.split(" ", 1)[1]

        try:
            token_data = decode_token(token_str)

            if not token_data:
                await self.app(scope, receive, send)
                return

            # Check blacklist
            if await check_blacklist(token_data.get("jti", "")):
                response = JSONResponse(
                    status_code=401,
                    content={"detail": "Token has been revoked"},
                )
                await response(scope, receive, send)
                return

            # Attach user data to request state
            scope.setdefault("state", {})
            scope["state"]["user"] = token_data.get("user", {})

        except Exception as e:
            logging.debug(f"Auth middleware token decode failed: {e}")
            # Don't block — let route dependencies handle enforcement

        await self.app(scope, receive, send)
