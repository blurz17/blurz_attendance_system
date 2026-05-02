"""
Auth routes — login, activation, token refresh, logout, password management.
No /signup endpoint — admins create users via the admin service.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import timedelta

from core.db.main import get_session
from core.db.config import config
from core.db.redis import add_to_blacklist, check_blacklist
from core.security import (
    create_jwt_token,
    verify_password,
    CreationSafeLink,
)
from core.dependencies import AccessTokenBearer, RefreshToken, get_current_user
from core.auth.service import get_user_by_email, activate_user, reset_password, change_password
from core.auth.schema import (
    LoginRequest,
    ActivationRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    UserInfo,
)
from core.errors import (
    UserNotFound,
    InvalidCredentials,
    AccountNotActive,
    PasswordAlreadyReset,
    DataNotFound,
    UserAlreadyActive,
)
from core.services.celery.celery_tasks import bg_send_mail
from core.db.models import User

auth_router = APIRouter()

# Token TTLs
REFRESH_TTL = timedelta(days=config.refresh_token_expiary)
ACCESS_TTL = timedelta(minutes=config.access_token_expiary)

# Safe URL serializers
email_verification_link = CreationSafeLink(config.jwt_secret, "email_verification_link")
password_reset_link = CreationSafeLink(config.password_secrete_reset, "password_reset_link")


# ── LOGIN ──────────────────────────────────────

@auth_router.post("/login")
async def login_user(
    user_data: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate with email + password. Returns access + refresh tokens."""
    user = await get_user_by_email(user_data.email, session)

    if not user:
        raise UserNotFound()
    if not user.is_active:
        raise AccountNotActive()
    if not verify_password(user_data.password, user.hashed_password):
        raise InvalidCredentials()

    payload = {"email": user.email, "id": str(user.id), "role": user.role.value}
    access_token = create_jwt_token(user_data=payload, expire=ACCESS_TTL)
    refresh_token = create_jwt_token(user_data=payload, expire=REFRESH_TTL, refresh=True)

    return JSONResponse(content={
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value,
    })


# ── ACCOUNT ACTIVATION ─────────────────────────

@auth_router.post("/verify/{token}")
async def activate_account(
    token: str,
    passwords: ActivationRequest,
    session: AsyncSession = Depends(get_session),
):
    """User clicks activation link → sets password → account becomes active."""
    data = email_verification_link.decode(token)

    if await check_blacklist(data["token_id"]):
        raise UserAlreadyActive()

    email = data.get("email")
    if not email:
        raise DataNotFound("Invalid activation link")

    if passwords.password != passwords.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    await activate_user(email, passwords.password, session)
    await add_to_blacklist(data["token_id"], exp=86400)

    return JSONResponse(
        content={"message": "Account activated successfully. You can now login."},
    )


# ── RESEND ACTIVATION EMAIL ────────────────────

@auth_router.post("/resend-verification")
async def resend_verification_email(
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
):
    """Resend the activation/verification email."""
    email = body.email.strip().lower()
    user = await get_user_by_email(email, session)

    if not user:
        return JSONResponse(content={"message": "If the email exists, a verification link has been sent."})

    if user.is_active:
        raise UserAlreadyActive()

    token = email_verification_link.create_url({"email": email})
    link = f"{config.frontend_url}/activate/{token}"

    bg_send_mail.delay(
        rec=[email],
        sub="Verify Your Account",
        html_path="verify_message.html",
        data_var={"link": link},
    )

    return JSONResponse(content={"message": "Verification link has been sent to your email."})


# ── ME ─────────────────────────────────────────

@auth_router.get("/me", response_model=UserInfo)
async def get_me(user: User = Depends(get_current_user)):
    """Return current authenticated user's info."""
    return user


# ── TOKEN REFRESH ──────────────────────────────

@auth_router.post("/refresh-token")
async def refresh_access_token(token: dict = Depends(RefreshToken())):
    """Exchange a refresh token for a new access + refresh token pair."""
    if not token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    new_access = create_jwt_token(user_data=token["user"], expire=ACCESS_TTL)
    new_refresh = create_jwt_token(user_data=token["user"], expire=REFRESH_TTL, refresh=True)
    await add_to_blacklist(token["jti"], exp=config.refresh_token_expiary * 86400)

    return JSONResponse(content={"access_token": new_access, "refresh_token": new_refresh})


# ── LOGOUT ─────────────────────────────────────

@auth_router.post("/logout")
async def logout(token: dict = Depends(AccessTokenBearer())):
    """Revoke the current access token."""
    await add_to_blacklist(token["jti"])
    return JSONResponse(content={"message": "Logged out successfully"})


# ── PASSWORD RESET ─────────────────────────────

@auth_router.post("/password-reset")
async def request_password_reset(
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
):
    """Send a password reset link to the user's email."""
    email = body.email.strip().lower()
    user = await get_user_by_email(email, session)

    if user:
        token = password_reset_link.create_url({"email": email})
        link = f"{config.frontend_url}/reset-password/{token}"
        bg_send_mail.delay(
            rec=[email],
            sub="Reset Your Password",
            html_path="password_reset_link.html",
            data_var={"link": link},
        )

    return JSONResponse(content={"message": "If the email exists, a reset link has been sent."})


@auth_router.post("/confirm-password/{token}")
async def confirm_password_reset(
    token: str,
    passwords: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
):
    """Reset password using the token from the reset email."""
    data = password_reset_link.decode(token, max_age=600)

    if await check_blacklist(data["token_id"]):
        raise PasswordAlreadyReset()

    if passwords.new_password != passwords.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    email = data.get("email")
    if not email:
        raise DataNotFound("Invalid reset link")

    await reset_password(email, passwords.new_password, session)
    await add_to_blacklist(data["token_id"], exp=600)

    return JSONResponse(content={"message": "Password has been reset successfully"})


# ── CHANGE PASSWORD ────────────────────────────

@auth_router.post("/change-password")
async def change_password_route(
    passwords: ChangePasswordRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Change password for the currently authenticated user."""
    if not verify_password(passwords.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    await change_password(user, passwords.new_password, session)
    return JSONResponse(content={"message": "Password updated successfully"})
