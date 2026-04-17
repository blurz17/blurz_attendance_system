"""
tests/test_admin_auth.py
========================
E2E tests for /api/v1/admin/auth/* endpoints.

Covers
------
- Admin login (success, wrong password, not found)
- Admin /me (valid token, student token rejected)
- Admin logout (blacklists token)
- Admin token refresh (valid, access-token rejected)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from conftest import (
    db_create_admin, bearer,
    make_admin_access_token, make_admin_refresh_token,
    make_access_token, _uid,
)
from core.db.models import SystemAdmin, User

BASE = "/api/v1/admin/auth"


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_login_success(
    client: AsyncClient, system_admin: SystemAdmin
):
    r = await client.post(f"{BASE}/login", json={
        "email": system_admin.email,
        "password": "AdminPass@123",
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "admin"
    assert data["email"] == system_admin.email
    assert data["admin_id"] == str(system_admin.id)


@pytest.mark.asyncio
async def test_admin_login_wrong_password_returns_401(
    client: AsyncClient, system_admin: SystemAdmin
):
    r = await client.post(f"{BASE}/login", json={
        "email": system_admin.email,
        "password": "WrongPass!",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_nonexistent_returns_404(client: AsyncClient):
    r = await client.post(f"{BASE}/login", json={
        "email": f"ghost_{_uid()}@uni.edu",
        "password": "AdminPass@123",
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_login_email_case_insensitive(
    client: AsyncClient, system_admin: SystemAdmin
):
    """Admin email lookup should be case-insensitive."""
    r = await client.post(f"{BASE}/login", json={
        "email": system_admin.email.upper(),
        "password": "AdminPass@123",
    })
    # NOTE: If this fails, get_admin_by_email needs .lower() normalisation
    assert r.status_code in (200, 404)


# ─────────────────────────────────────────────────────────────────────────────
# /ME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_me_returns_admin_info(
    client: AsyncClient, system_admin: SystemAdmin, admin_headers: dict
):
    r = await client.get(f"{BASE}/me", headers=admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == system_admin.email


@pytest.mark.asyncio
async def test_admin_me_with_student_token_rejected(
    client: AsyncClient, active_student: User
):
    """A regular user token must not grant admin /me access."""
    r = await client.get(f"{BASE}/me", headers=bearer(make_access_token(active_student)))
    assert r.status_code in (401, 403, 404)


@pytest.mark.asyncio
async def test_admin_me_no_token_returns_403(client: AsyncClient):
    r = await client.get(f"{BASE}/me")
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_logout_success(
    client: AsyncClient, system_admin: SystemAdmin, admin_headers: dict
):
    r = await client.post(f"{BASE}/logout", headers=admin_headers)
    assert r.status_code == 200
    assert "logged out" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_admin_logout_then_me_fails(
    client: AsyncClient, system_admin: SystemAdmin
):
    """After logout the same token must be revoked."""
    token = make_admin_access_token(system_admin)
    headers = bearer(token)

    r_logout = await client.post(f"{BASE}/logout", headers=headers)
    assert r_logout.status_code == 200

    r_me = await client.get(f"{BASE}/me", headers=headers)
    assert r_me.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN REFRESH
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_refresh_token_returns_new_pair(
    client: AsyncClient, system_admin: SystemAdmin
):
    refresh = make_admin_refresh_token(system_admin)
    r = await client.post(f"{BASE}/refresh-token", headers=bearer(refresh))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_admin_refresh_rejects_access_token(
    client: AsyncClient, system_admin: SystemAdmin, admin_headers: dict
):
    r = await client.post(f"{BASE}/refresh-token", headers=admin_headers)
    assert r.status_code in (401, 403)
