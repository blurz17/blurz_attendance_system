"""
Admin Auth schemas — Pydantic models for system administrator authentication.
"""
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional


class AdminLoginRequest(BaseModel):
    email: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=72)


class AdminTokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    admin_id: str
    email: str
    role: str


class AdminInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
