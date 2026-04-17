"""
Admin Auth routes — login, refresh, logout, and me for system administrators.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import timedelta

from core.db.main import get_session
from core.db.config import config
from core.db.redis import add_to_blacklist
from core.security import create_jwt_token, verify_password
from core.admin.auth.service import get_admin_by_email
from core.admin.auth.schema import AdminLoginRequest, AdminInfo
from core.errors import InvalidCredentials, UserNotFound
from core.dependencies import AccessTokenBearer, RefreshToken, get_current_admin

admin_auth_router = APIRouter()

ACCESS_TTL = timedelta(minutes=config.access_token_expiary)
REFRESH_TTL = timedelta(days=config.refresh_token_expiary)


@admin_auth_router.post("/login")
async def admin_login(
    data: AdminLoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Admin-specific login. Isolated from the student/professor User table."""
    admin = await get_admin_by_email(data.email.strip().lower(), session)
    if not admin:
        raise UserNotFound("Admin account not found")
    if not verify_password(data.password, admin.hashed_password):
        raise InvalidCredentials()

    payload = {"email": admin.email, "id": str(admin.id), "role": "admin"}
    access_token = create_jwt_token(user_data=payload, expire=ACCESS_TTL)
    refresh_token = create_jwt_token(user_data=payload, expire=REFRESH_TTL, refresh=True)

    return JSONResponse(content={
        "message": "Admin login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "admin_id": str(admin.id),
        "email": admin.email,
        "role": "admin",
    })


@admin_auth_router.get("/me", response_model=AdminInfo)
async def get_me(admin=Depends(get_current_admin)):
    """Return current authenticated admin's info."""
    return admin


@admin_auth_router.post("/refresh-token")
async def refresh_admin_token(token: dict = Depends(RefreshToken())):
    """Exchange a refresh token for a new token pair."""
    if not token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    new_access = create_jwt_token(user_data=token["user"], expire=ACCESS_TTL)
    new_refresh = create_jwt_token(user_data=token["user"], expire=REFRESH_TTL, refresh=True)
    await add_to_blacklist(token["jti"], exp=config.refresh_token_expiary * 86400)

    return JSONResponse(content={"access_token": new_access, "refresh_token": new_refresh})


@admin_auth_router.post("/logout")
async def admin_logout(token: dict = Depends(AccessTokenBearer())):
    """Revoke the current access token."""
    await add_to_blacklist(token["jti"])
    return JSONResponse(content={"message": "Logged out successfully"})
