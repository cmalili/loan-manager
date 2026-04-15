"""Schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Credentials payload for logging in."""

    email: str
    password: str


class AuthenticatedUserRead(BaseModel):
    """Authenticated user response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    """Token response for successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user: AuthenticatedUserRead
