"""
tests/test_security.py
======================
Unit tests for security utilities (no HTTP, no DB).

Covers
------
- Password hashing & verification
- JWT access token creation, decoding, expiry
- JWT refresh token flag
- QR token generation & HMAC verification
- BUG-#1: timezone-naive datetime comparison in verify_qr_token
- BUG-#2: QRCodeExpired/InvalidToken swallowed inside verify_qr_token try-block
- Safe URL link creation & decode (itsdangerous)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta

import pytest

from core.security import (
    generate_hashed_password,
    verify_password,
    create_jwt_token,
    decode_token,
    generate_qr_token,
    verify_qr_token,
    CreationSafeLink,
)
from core.errors import InvalidToken, TokenExpired, QRCodeExpired
from core.db.config import config


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────────────────────────────────────

def test_hash_and_verify_correct_password():
    hashed = generate_hashed_password("TestPass@123")
    assert verify_password("TestPass@123", hashed) is True


def test_verify_wrong_password_returns_false():
    hashed = generate_hashed_password("TestPass@123")
    assert verify_password("WrongPass!", hashed) is False


def test_hash_is_different_each_call():
    h1 = generate_hashed_password("samepassword")
    h2 = generate_hashed_password("samepassword")
    assert h1 != h2  # bcrypt salt differs


def test_password_over_72_chars_truncated_consistently():
    """bcrypt silently truncates at 72 bytes — both passwords hash the same."""
    base = "A" * 72
    long_pw = base + "extra_ignored_suffix"
    hashed = generate_hashed_password(base)
    # The 72-char version should match
    assert verify_password(base, hashed) is True


# ─────────────────────────────────────────────────────────────────────────────
# JWT TOKENS
# ─────────────────────────────────────────────────────────────────────────────

def test_access_token_encodes_user_data():
    payload = {"email": "test@uni.edu", "id": "abc123", "role": "student"}
    token = create_jwt_token(user_data=payload, expire=timedelta(minutes=30))
    decoded = decode_token(token)
    assert decoded["user"]["email"] == "test@uni.edu"
    assert decoded["user"]["role"] == "student"


def test_access_token_refresh_flag_is_false():
    token = create_jwt_token(
        user_data={"email": "t@t.com"}, expire=timedelta(minutes=30), refresh=False
    )
    decoded = decode_token(token)
    assert decoded["refresh_token"] is False


def test_refresh_token_refresh_flag_is_true():
    token = create_jwt_token(
        user_data={"email": "t@t.com"}, expire=timedelta(days=7), refresh=True
    )
    decoded = decode_token(token)
    assert decoded["refresh_token"] is True


def test_each_token_has_unique_jti():
    payload = {"email": "t@t.com"}
    t1 = create_jwt_token(user_data=payload, expire=timedelta(minutes=30))
    t2 = create_jwt_token(user_data=payload, expire=timedelta(minutes=30))
    assert decode_token(t1)["jti"] != decode_token(t2)["jti"]


def test_expired_token_raises_token_expired():
    token = create_jwt_token(
        user_data={"email": "t@t.com"}, expire=timedelta(seconds=-1)
    )
    with pytest.raises(TokenExpired):
        decode_token(token)


def test_invalid_token_string_raises_invalid_token():
    with pytest.raises(InvalidToken):
        decode_token("not.a.valid.token")


def test_tampered_token_raises_invalid_token():
    token = create_jwt_token(
        user_data={"email": "t@t.com"}, expire=timedelta(minutes=30)
    )
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(InvalidToken):
        decode_token(tampered)


# ─────────────────────────────────────────────────────────────────────────────
# QR TOKEN  (HMAC-SHA256)
# ─────────────────────────────────────────────────────────────────────────────

def _future_expires_at(minutes: int = 15) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(tzinfo=None).isoformat()


def _past_expires_at(minutes: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).replace(tzinfo=None).isoformat()


def test_generate_and_verify_qr_token():
    token = generate_qr_token(
        course_id="course-1",
        week_number=3,
        expires_at=_future_expires_at(),
    )
    payload = verify_qr_token(token)
    assert payload["course_id"] == "course-1"
    assert payload["week_number"] == 3


def test_qr_token_with_section_id():
    token = generate_qr_token(
        course_id="c1",
        week_number=1,
        expires_at=_future_expires_at(),
        section_id="sec-42",
    )
    payload = verify_qr_token(token)
    assert payload["section_id"] == "sec-42"


def test_qr_token_without_section_id_is_none():
    token = generate_qr_token(
        course_id="c2", week_number=2, expires_at=_future_expires_at()
    )
    payload = verify_qr_token(token)
    assert payload["section_id"] is None


def test_tampered_qr_signature_raises_invalid_token():
    token = generate_qr_token(
        course_id="c1", week_number=1, expires_at=_future_expires_at()
    )
    parts = token.split(".")
    tampered = parts[0] + ".badsignaturexxx"
    with pytest.raises(InvalidToken):
        verify_qr_token(tampered)


def test_tampered_qr_payload_raises_invalid_token():
    """Modifying the base64 payload invalidates the HMAC."""
    token = generate_qr_token(
        course_id="c1", week_number=1, expires_at=_future_expires_at()
    )
    encoded, sig = token.split(".", 1)
    # Flip a character in the encoded payload
    bad_encoded = encoded[:-3] + "XXX"
    with pytest.raises(InvalidToken):
        verify_qr_token(bad_encoded + "." + sig)


def test_expired_qr_token_raises_qr_code_expired():
    """
    BUG-#1 & BUG-#2 CHECK:
    An expired-datetime token must raise QRCodeExpired, not be swallowed.
    """
    token = generate_qr_token(
        course_id="c1", week_number=1, expires_at=_past_expires_at()
    )
    with pytest.raises(QRCodeExpired):
        verify_qr_token(token)


def test_malformed_token_no_dot_raises_invalid_token():
    with pytest.raises(InvalidToken):
        verify_qr_token("nodotintoken")


def test_malformed_base64_payload_raises_invalid_token():
    with pytest.raises(InvalidToken):
        verify_qr_token("!!!invalid_base64!!!.somesig")


# ─────────────────────────────────────────────────────────────────────────────
# SAFE URL LINK  (itsdangerous)
# ─────────────────────────────────────────────────────────────────────────────

def test_create_and_decode_safe_link():
    link = CreationSafeLink(config.jwt_secret, "test_salt")
    token = link.create_url({"email": "user@uni.edu"})
    data = link.decode(token, max_age=3600)
    assert data["email"] == "user@uni.edu"
    assert "token_id" in data  # auto-injected UUID


def test_each_link_token_has_unique_token_id():
    link = CreationSafeLink(config.jwt_secret, "test_salt")
    t1 = link.create_url({"email": "a@uni.edu"})
    t2 = link.create_url({"email": "a@uni.edu"})
    d1 = link.decode(t1)
    d2 = link.decode(t2)
    assert d1["token_id"] != d2["token_id"]


def test_wrong_salt_raises_invalid_token():
    link_a = CreationSafeLink(config.jwt_secret, "salt_a")
    link_b = CreationSafeLink(config.jwt_secret, "salt_b")
    token = link_a.create_url({"email": "x@uni.edu"})
    with pytest.raises(InvalidToken):
        link_b.decode(token)


def test_expired_safe_link_raises_token_expired():
    link = CreationSafeLink(config.jwt_secret, "test_salt")
    token = link.create_url({"email": "y@uni.edu"})
    with pytest.raises(TokenExpired):
        link.decode(token, max_age=0)  # max_age=0 → immediately expired
