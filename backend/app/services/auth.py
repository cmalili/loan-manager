"""Authentication service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User


class AuthenticationError(ValueError):
    """Raised when credentials are invalid."""


class InactiveUserError(ValueError):
    """Raised when an inactive user attempts to authenticate."""


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by email address."""

    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """Authenticate one user by email and password."""

    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise InactiveUserError("User account is inactive")
    return user


def issue_access_token_for_user(user: User) -> str:
    """Issue a signed bearer token for the given user."""

    return create_access_token(subject=str(user.id), role=user.role)


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetch one user by UUID."""

    return db.get(User, user_id)
