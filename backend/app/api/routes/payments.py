"""Payment API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment import (
    PaymentBorrowerNotFoundError,
    PaymentLoanNotFoundError,
    PaymentRecorderNotFoundError,
    PaymentValidationError,
    record_payment,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def record_payment_endpoint(
    payment_in: PaymentCreate, db: Session = Depends(get_db)
) -> PaymentRead:
    """Record a payment and apply allocations."""

    try:
        return record_payment(db, payment_in)
    except (
        PaymentLoanNotFoundError,
        PaymentBorrowerNotFoundError,
        PaymentRecorderNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PaymentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
