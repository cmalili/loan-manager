"""Borrower API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.borrower import BorrowerCreate, BorrowerRead, BorrowerUpdate
from app.schemas.loan import LoanRead
from app.services.borrower import (
    BorrowerNotFoundError,
    create_borrower,
    deactivate_borrower,
    get_borrower,
    list_borrowers,
    update_borrower,
)
from app.services.reporting import list_borrower_loan_history

router = APIRouter(prefix="/borrowers", tags=["borrowers"])


@router.get("/", response_model=list[BorrowerRead])
def list_borrowers_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BorrowerRead]:
    """Return all borrowers."""

    return list_borrowers(db)


@router.get("/{borrower_id}", response_model=BorrowerRead)
def get_borrower_endpoint(
    borrower_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BorrowerRead:
    """Return one borrower by ID."""

    try:
        return get_borrower(db, borrower_id)
    except BorrowerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{borrower_id}/loans", response_model=list[LoanRead])
def list_borrower_loans_endpoint(
    borrower_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LoanRead]:
    """Return the loan history for one borrower."""

    try:
        return list_borrower_loan_history(db, borrower_id)
    except BorrowerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/",
    response_model=BorrowerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_borrower_endpoint(
    borrower_in: BorrowerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user),
) -> BorrowerRead:
    """Create a borrower."""

    return create_borrower(db, borrower_in, acting_user_id=current_user.id)


@router.patch("/{borrower_id}", response_model=BorrowerRead)
def update_borrower_endpoint(
    borrower_id: UUID,
    borrower_in: BorrowerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user),
) -> BorrowerRead:
    """Partially update a borrower."""

    try:
        return update_borrower(
            db,
            borrower_id,
            borrower_in,
            acting_user_id=current_user.id,
        )
    except BorrowerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{borrower_id}/deactivate", response_model=BorrowerRead)
def deactivate_borrower_endpoint(
    borrower_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user),
) -> BorrowerRead:
    """Deactivate a borrower while preserving history."""

    try:
        return deactivate_borrower(db, borrower_id, acting_user_id=current_user.id)
    except BorrowerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
