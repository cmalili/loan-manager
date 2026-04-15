"""Borrower service layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate
from app.services.audit import record_audit_log, snapshot_model


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
    db.flush()
    record_audit_log(
        db,
        user_id=None,
        entity_type="borrower",
        entity_id=borrower.id,
        action_type="create",
        before_state=None,
        after_state=snapshot_model(borrower),
    )
    db.commit()
    db.refresh(borrower)
    return borrower


def update_borrower(db: Session, borrower_id: UUID, borrower_in: BorrowerUpdate) -> Borrower:
    """Apply a partial update to an existing borrower."""

    borrower = get_borrower(db, borrower_id)
    before_state = snapshot_model(borrower)

    for field_name, value in borrower_in.model_dump(exclude_unset=True).items():
        setattr(borrower, field_name, value)

    db.add(borrower)
    db.flush()
    record_audit_log(
        db,
        user_id=None,
        entity_type="borrower",
        entity_id=borrower.id,
        action_type="update",
        before_state=before_state,
        after_state=snapshot_model(borrower),
    )
    db.commit()
    db.refresh(borrower)
    return borrower


def deactivate_borrower(db: Session, borrower_id: UUID) -> Borrower:
    """Mark a borrower inactive while preserving history."""

    borrower = get_borrower(db, borrower_id)
    before_state = snapshot_model(borrower)
    borrower.status = "inactive"
    db.add(borrower)
    db.flush()
    record_audit_log(
        db,
        user_id=None,
        entity_type="borrower",
        entity_id=borrower.id,
        action_type="status_change",
        before_state=before_state,
        after_state=snapshot_model(borrower),
    )
    db.commit()
    db.refresh(borrower)
    return borrower
