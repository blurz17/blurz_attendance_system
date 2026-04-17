"""
Auth schemas — Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    student = "student"
    professor = "professor"


# ──────────────────────────────────────────────
# Auth Request/Response Schemas
# ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=72)


class TokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    role: str


class ActivationRequest(BaseModel):
    """When user clicks activation link, they set their password."""
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


# ──────────────────────────────────────────────
# User Display Schemas
# ──────────────────────────────────────────────

class UserInfo(BaseModel):
    id: uuid.UUID
    university_id: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
