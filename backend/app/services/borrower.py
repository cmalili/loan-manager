"""Borrower service layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate


class BorrowerNotFoundError(LookupError):
    """Raised when a borrower record cannot be found."""


def list_borrowers(db: Session) -> list[Borrower]:
    """Return all borrowers ordered by creation time descending."""

    statement = select(Borrower).order_by(Borrower.created_at.desc())
    return list(db.scalars(statement).all())


def get_borrower(db: Session, borrower_id: UUID) -> Borrower:
    """Fetch a borrower by ID or raise if it does not exist."""

    borrower = db.get(Borrower, borrower_id)
    if borrower is None:
        raise BorrowerNotFoundError(f"Borrower {borrower_id} was not found")
    return borrower


def create_borrower(db: Session, borrower_in: BorrowerCreate) -> Borrower:
    """Create and persist a borrower."""

    borrower = Borrower(**borrower_in.model_dump())
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def update_borrower(db: Session, borrower_id: UUID, borrower_in: BorrowerUpdate) -> Borrower:
    """Apply a partial update to an existing borrower."""

    borrower = get_borrower(db, borrower_id)

    for field_name, value in borrower_in.model_dump(exclude_unset=True).items():
        setattr(borrower, field_name, value)

    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def deactivate_borrower(db: Session, borrower_id: UUID) -> Borrower:
    """Mark a borrower inactive while preserving history."""

    borrower = get_borrower(db, borrower_id)
    borrower.status = "inactive"
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower
