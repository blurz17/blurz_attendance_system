"""
FastAPI dependencies: token bearers, current user, role checking.
"""
import logging
from fastapi.security import HTTPBearer
from fastapi import status, Request, Depends
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from core.security import decode_token
from core.db.redis import check_blacklist
from core.db.main import get_session
from core.db.models import User
from core.errors import (
    InvalidToken, RefreshTokenRequired, AccessTokenRequired,
    InsufficientPermission, AccountNotActive,
)


# ── TOKEN BEARERS ──────────────────────────────

class AccessTokenBearer(HTTPBearer):
    """Validates access tokens (not refresh)."""

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)
        token = decode_token(credentials.credentials)

        if not token:
            raise InvalidToken()
        if await check_blacklist(token["jti"]):
            raise HTTPException(status_code=403, detail="Token has been revoked. Please login again.")
        if token.get("refresh_token"):
            raise AccessTokenRequired()

        return token


class RefreshToken(HTTPBearer):
    """Validates refresh tokens (not access)."""

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)
        token = decode_token(credentials.credentials)

        if not token:
            raise InvalidToken()
        if await check_blacklist(token["jti"]):
            raise HTTPException(status_code=403, detail="Token has been revoked. Please login again.")
        if not token.get("refresh_token"):
            raise RefreshTokenRequired()

        return token


# ── CURRENT USER / ADMIN ───────────────────────

async def get_current_user(
    token: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Extract the current user from the access token."""
    from core.auth.service import get_user_by_email

    try:
        user = await get_user_by_email(token["user"]["email"], session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")


async def get_current_admin(
    token: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    """Extract the current admin from the access token."""
    from core.admin.auth.service import get_admin_by_email

    try:
        admin = await get_admin_by_email(token["user"]["email"], session)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error fetching admin: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin")


# ── ROLE CHECKER ───────────────────────────────

class RoleChecker:
    """Dependency: checks if the current user has the required role.
    Usage: Depends(RoleChecker(["professor"]))
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not user.is_active:
            raise AccountNotActive()
        if user.role not in self.allowed_roles:
            raise InsufficientPermission()
        return user