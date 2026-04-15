"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import (
    AuthenticationError,
    InactiveUserError,
    authenticate_user,
    issue_access_token_for_user,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login_endpoint(login_in: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate one internal user and return a bearer token."""

    try:
        user = authenticate_user(db, email=login_in.email, password=login_in.password)
    except (AuthenticationError, InactiveUserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        access_token=issue_access_token_for_user(user),
        user=user,
    )
