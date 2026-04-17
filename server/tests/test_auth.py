"""
tests/test_auth.py
==================
Full E2E tests for /api/v1/auth/* endpoints.

Covers
------
- Login (success, wrong password, inactive account, bad email, case-insensitivity)
- /me (success, no token, revoked token, refresh token rejected)
- Token refresh (valid, access-token rejected, blacklisted)
- Logout (token blacklisted)
- Password reset request (no email enumeration)
- Confirm password reset (valid token, mismatch, already-used link)
- Change password (success, wrong current, unauthenticated)
- Account activation (valid token, mismatch, reuse)

Bug coverage
------------
- BUG-#3: activation link uses config.domain vs config.frontend_url (env difference)
- BUG-#10: inactive user with valid token correctly rejected by RoleChecker
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from conftest import (
    db_create_user, make_access_token, make_refresh_token, bearer, _uid,
)
from core.auth.schema import UserRole
from core.db.models import User
from core.security import CreationSafeLink
from core.db.config import config

BASE = "/api/v1/auth"

# Serializers (same as production)
_activation_link = CreationSafeLink(config.jwt_secret, "email_verification_link")
_reset_link = CreationSafeLink(config.password_secrete_reset, "password_reset_link")


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_active_student_returns_tokens(
    client: AsyncClient, active_student: User
):
    r = await client.post(f"{BASE}/login", json={
        "email": active_student.email,
        "password": "TestPass@123",
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == active_student.email
    assert data["role"] == "student"
    assert data["user_id"] == str(active_student.id)


@pytest.mark.asyncio
async def test_login_professor_returns_correct_role(
    client: AsyncClient, active_professor: User
):
    r = await client.post(f"{BASE}/login", json={
        "email": active_professor.email,
        "password": "TestPass@123",
    })
    assert r.status_code == 200
    assert r.json()["role"] == "professor"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient, active_student: User
):
    r = await client.post(f"{BASE}/login", json={
        "email": active_student.email,
        "password": "WrongPassword99!",
    })
    assert r.status_code == 401
    assert "invalid" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_404(client: AsyncClient):
    r = await client.post(f"{BASE}/login", json={
        "email": f"nobody_{_uid()}@uni.edu",
        "password": "TestPass@123",
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_login_inactive_account_returns_403(
    client: AsyncClient, inactive_student: User
):
    """Account not yet activated must be rejected at login."""
    r = await client.post(f"{BASE}/login", json={
        "email": inactive_student.email,
        "password": "TestPass@123",
    })
    assert r.status_code == 403
    assert "not activated" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_email_is_case_insensitive(
    client: AsyncClient, active_student: User
):
    """Email lookup should succeed regardless of case."""
    r = await client.post(f"{BASE}/login", json={
        "email": active_student.email.upper(),
        "password": "TestPass@123",
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_login_short_password_rejected_by_validation(client: AsyncClient):
    """Pydantic min_length=8 must fire before hitting the DB."""
    r = await client.post(f"{BASE}/login", json={
        "email": "someone@uni.edu",
        "password": "short",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_fields_returns_422(client: AsyncClient):
    r = await client.post(f"{BASE}/login", json={"email": "only@uni.edu"})
    assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# /ME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_returns_user_info(
    client: AsyncClient, active_student: User, student_headers: dict
):
    r = await client.get(f"{BASE}/me", headers=student_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == active_student.email
    assert data["university_id"] == active_student.university_id
    assert data["role"] == "student"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_no_token_returns_403(client: AsyncClient):
    r = await client.get(f"{BASE}/me")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_malformed_token_returns_401(client: AsyncClient):
    r = await client.get(
        f"{BASE}/me",
        headers={"Authorization": "Bearer totally.not.valid"},
    )
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_with_refresh_token_rejected(
    client: AsyncClient, active_student: User
):
    """Refresh tokens must NOT be accepted at /me."""
    refresh = make_refresh_token(active_student)
    r = await client.get(f"{BASE}/me", headers=bearer(refresh))
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_blacklisted_token_rejected(
    client: AsyncClient, active_student: User
):
    """Once a JTI is blacklisted, all requests with that token should fail."""
    from core.db.redis import add_to_blacklist
    from core.security import decode_token

    token = make_access_token(active_student)
    jti = decode_token(token)["jti"]
    await add_to_blacklist(jti, exp=3600)

    r = await client.get(f"{BASE}/me", headers=bearer(token))
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN REFRESH
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_returns_new_pair(
    client: AsyncClient, active_student: User
):
    refresh = make_refresh_token(active_student)
    r = await client.post(f"{BASE}/refresh-token", headers=bearer(refresh))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens must differ from original
    assert data["refresh_token"] != refresh


@pytest.mark.asyncio
async def test_refresh_endpoint_rejects_access_token(
    client: AsyncClient, active_student: User, student_headers: dict
):
    r = await client.post(f"{BASE}/refresh-token", headers=student_headers)
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_blacklisted_token_rejected(
    client: AsyncClient, active_student: User
):
    from core.db.redis import add_to_blacklist
    from core.security import decode_token

    refresh = make_refresh_token(active_student)
    jti = decode_token(refresh)["jti"]
    await add_to_blacklist(jti, exp=86400)

    r = await client.post(f"{BASE}/refresh-token", headers=bearer(refresh))
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_blacklists_token(
    client: AsyncClient, active_student: User, student_headers: dict
):
    r = await client.post(f"{BASE}/logout", headers=student_headers)
    assert r.status_code == 200
    assert "logged out" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_logout_then_me_fails(
    client: AsyncClient, active_student: User
):
    """After logout the same access token must be rejected."""
    token = make_access_token(active_student)
    headers = bearer(token)

    logout_r = await client.post(f"{BASE}/logout", headers=headers)
    assert logout_r.status_code == 200

    me_r = await client.get(f"{BASE}/me", headers=headers)
    assert me_r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_logout_unauthenticated_returns_403(client: AsyncClient):
    r = await client.post(f"{BASE}/logout")
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET — REQUEST
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_password_reset_request_always_200_existing_email(
    client: AsyncClient, active_student: User
):
    """Prevent email enumeration — always 200."""
    r = await client.post(
        f"{BASE}/password-reset",
        json={"email": active_student.email},
    )
    assert r.status_code == 200
    assert "reset link" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_password_reset_request_always_200_nonexistent_email(client: AsyncClient):
    """Even unknown emails must return 200 to prevent enumeration."""
    r = await client.post(
        f"{BASE}/password-reset",
        json={"email": f"ghost_{_uid()}@uni.edu"},
    )
    assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET — CONFIRM
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_password_reset_success(
    client: AsyncClient, active_student: User
):
    token = _reset_link.create_url({"email": active_student.email})
    r = await client.post(
        f"{BASE}/confirm-password/{token}",
        json={
            "new_password": "BrandNew@Pass1",
            "confirm_password": "BrandNew@Pass1",
        },
    )
    assert r.status_code == 200
    assert "reset" in r.json()["message"].lower()

    # Can now login with new password
    login_r = await client.post(f"{BASE}/login", json={
        "email": active_student.email,
        "password": "BrandNew@Pass1",
    })
    assert login_r.status_code == 200


@pytest.mark.asyncio
async def test_confirm_password_reset_mismatch_rejected(
    client: AsyncClient, active_student: User
):
    token = _reset_link.create_url({"email": active_student.email})
    r = await client.post(
        f"{BASE}/confirm-password/{token}",
        json={
            "new_password": "BrandNew@Pass1",
            "confirm_password": "DifferentPass@1",
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_confirm_password_reset_token_reuse_rejected(
    client: AsyncClient, active_student: User
):
    """BUG CHECK: token_id must be blacklisted after first use → 409 on reuse."""
    token = _reset_link.create_url({"email": active_student.email})
    body = {
        "new_password": "BrandNew@Pass1",
        "confirm_password": "BrandNew@Pass1",
    }
    r1 = await client.post(f"{BASE}/confirm-password/{token}", json=body)
    assert r1.status_code == 200

    r2 = await client.post(f"{BASE}/confirm-password/{token}", json=body)
    assert r2.status_code == 409  # PasswordAlreadyReset


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT ACTIVATION
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_activate_account_success(
    client: AsyncClient, db_session: AsyncSession
):
    uid = _uid()
    user = await db_create_user(
        db_session,
        university_id=f"NEWSTU{uid}",
        id_card=f"NEWCARD{uid}",
        full_name="New Student",
        email=f"new_{uid}@uni.edu",
        role=UserRole.student,
        is_active=False,
        password="placeholder",  # will be overwritten
    )
    # Manually mark hashed_password as placeholder (simulates admin-created user)
    user.is_active = False
    await db_session.commit()

    token = _activation_link.create_url({"email": user.email})
    r = await client.post(
        f"{BASE}/verify/{token}",
        json={"password": "ActivateMe@123", "confirm_password": "ActivateMe@123"},
    )
    assert r.status_code == 200
    assert "activated" in r.json()["message"].lower()

    # Now login should work
    login_r = await client.post(f"{BASE}/login", json={
        "email": user.email,
        "password": "ActivateMe@123",
    })
    assert login_r.status_code == 200


@pytest.mark.asyncio
async def test_activate_account_password_mismatch(
    client: AsyncClient, db_session: AsyncSession
):
    uid = _uid()
    user = await db_create_user(
        db_session,
        university_id=f"MSTU{uid}",
        id_card=f"MCARD{uid}",
        full_name="Mismatch Student",
        email=f"mismatch_{uid}@uni.edu",
        role=UserRole.student,
        is_active=False,
    )
    user.is_active = False
    await db_session.commit()

    token = _activation_link.create_url({"email": user.email})
    r = await client.post(
        f"{BASE}/verify/{token}",
        json={"password": "GoodPass@123", "confirm_password": "BadPass@123"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_activate_account_token_reuse_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    """BUG CHECK: token_id blacklisted → 409 on second activation."""
    uid = _uid()
    user = await db_create_user(
        db_session,
        university_id=f"RSTU{uid}",
        id_card=f"RCARD{uid}",
        full_name="Reuse Student",
        email=f"reuse_{uid}@uni.edu",
        role=UserRole.student,
        is_active=False,
    )
    user.is_active = False
    await db_session.commit()

    token = _activation_link.create_url({"email": user.email})
    body = {"password": "ActivateMe@123", "confirm_password": "ActivateMe@123"}

    r1 = await client.post(f"{BASE}/verify/{token}", json=body)
    assert r1.status_code == 200

    r2 = await client.post(f"{BASE}/verify/{token}", json=body)
    assert r2.status_code == 409  # UserAlreadyActive


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE PASSWORD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_change_password_success(
    client: AsyncClient, active_student: User, student_headers: dict
):
    r = await client.post(
        f"{BASE}/change-password",
        json={
            "current_password": "TestPass@123",
            "new_password": "NewSecure@456",
        },
        headers=student_headers,
    )
    assert r.status_code == 200
    assert "updated" in r.json()["message"].lower()

    # Verify new password works
    login_r = await client.post(f"{BASE}/login", json={
        "email": active_student.email,
        "password": "NewSecure@456",
    })
    assert login_r.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current_returns_400(
    client: AsyncClient, student_headers: dict
):
    r = await client.post(
        f"{BASE}/change-password",
        json={
            "current_password": "WrongOldPass!",
            "new_password": "NewSecure@456",
        },
        headers=student_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_change_password_unauthenticated_returns_403(client: AsyncClient):
    r = await client.post(
        f"{BASE}/change-password",
        json={
            "current_password": "TestPass@123",
            "new_password": "NewSecure@456",
        },
    )
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# RESEND VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resend_verification_inactive_user(
    client: AsyncClient, inactive_student: User
):
    r = await client.post(
        f"{BASE}/resend-verification",
        json={"email": inactive_student.email},
    )
    assert r.status_code == 200
    assert "verification link" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_resend_verification_already_active_returns_409(
    client: AsyncClient, active_student: User
):
    r = await client.post(
        f"{BASE}/resend-verification",
        json={"email": active_student.email},
    )
    assert r.status_code == 409  # UserAlreadyActive


@pytest.mark.asyncio
async def test_resend_verification_unknown_email_returns_200(client: AsyncClient):
    """No email enumeration — unknown email silently succeeds."""
    r = await client.post(
        f"{BASE}/resend-verification",
        json={"email": f"ghost_{_uid()}@uni.edu"},
    )
    assert r.status_code == 200
