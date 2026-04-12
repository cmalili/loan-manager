"""Loan API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.loan import LoanCreate, LoanRead
from app.services.loan import (
    ActiveLoanConflictError,
    LoanBorrowerNotFoundError,
    LoanCreatorNotFoundError,
    LoanValidationError,
    create_loan,
)

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan_endpoint(loan_in: LoanCreate, db: Session = Depends(get_db)) -> LoanRead:
    """Create a loan after enforcing Phase 3 validation rules."""

    try:
        return create_loan(db, loan_in)
    except (LoanBorrowerNotFoundError, LoanCreatorNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ActiveLoanConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except LoanValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
