"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings used by application infrastructure."""

    auth_secret_key: str
    access_token_expire_minutes: int = 60


def get_settings() -> Settings:
    """Build settings from environment variables."""

    secret = os.getenv("AUTH_SECRET_KEY", "dev-auth-secret-change-me")
    expires_in = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    return Settings(
        auth_secret_key=secret,
        access_token_expire_minutes=expires_in,
    )


settings = get_settings()
