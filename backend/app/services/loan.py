"""Loan service layer."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.models.loan import Loan
from app.models.user import User
from app.schemas.loan import LoanCreate
from app.services.repayment_schedule import add_months, build_schedule_items


WEEKLY_RATE = Decimal("8.00")
MONTHLY_RATE = Decimal("30.00")
ALLOWED_CREATE_STATUSES = {"draft", "active"}
STANDARD_GRACE_PERIOD_DAYS = 7


class LoanValidationError(ValueError):
    """Raised when a loan payload violates business rules."""


class LoanBorrowerNotFoundError(LookupError):
    """Raised when the borrower for a loan does not exist."""


class LoanCreatorNotFoundError(LookupError):
    """Raised when the creator user for a loan does not exist."""


class ActiveLoanConflictError(ValueError):
    """Raised when the borrower already has an active loan."""


def calculate_end_date(start_date: date, repayment_frequency: str, term_length: int) -> date:
    """Calculate the loan end date from term and repayment frequency."""

    if repayment_frequency == "weekly":
        from datetime import timedelta

        return start_date + timedelta(weeks=term_length)
    if repayment_frequency == "monthly":
        return add_months(start_date, term_length)
    raise LoanValidationError(f"Unsupported repayment frequency: {repayment_frequency}")


def get_periodic_interest_rate(repayment_frequency: str) -> Decimal:
    """Return the standard periodic rate for the selected frequency."""

    if repayment_frequency == "weekly":
        return WEEKLY_RATE
    if repayment_frequency == "monthly":
        return MONTHLY_RATE
    raise LoanValidationError(f"Unsupported repayment frequency: {repayment_frequency}")


def create_loan(db: Session, loan_in: LoanCreate) -> Loan:
    """Create and persist a loan while enforcing V1 business rules."""

    borrower = db.get(Borrower, loan_in.borrower_id)
    if borrower is None:
        raise LoanBorrowerNotFoundError(f"Borrower {loan_in.borrower_id} was not found")

    creator = db.get(User, loan_in.created_by_user_id)
    if creator is None:
        raise LoanCreatorNotFoundError(f"User {loan_in.created_by_user_id} was not found")

    if loan_in.status not in ALLOWED_CREATE_STATUSES:
        raise LoanValidationError(
            f"Loans may only be created with status draft or active, not {loan_in.status}"
        )

    if loan_in.grace_period_days != STANDARD_GRACE_PERIOD_DAYS:
        raise LoanValidationError(
            f"Grace period must be {STANDARD_GRACE_PERIOD_DAYS} days in Version 1"
        )

    if loan_in.status == "active":
        active_loan = db.scalar(
            select(Loan).where(
                Loan.borrower_id == loan_in.borrower_id,
                Loan.status == "active",
            )
        )
        if active_loan is not None:
            raise ActiveLoanConflictError(
                f"Borrower {loan_in.borrower_id} already has an active loan"
            )

    periodic_interest_rate = get_periodic_interest_rate(loan_in.repayment_frequency)
    end_date = calculate_end_date(
        loan_in.start_date,
        loan_in.repayment_frequency,
        loan_in.term_length,
    )

    loan = Loan(
        borrower_id=loan_in.borrower_id,
        created_by_user_id=loan_in.created_by_user_id,
        principal_amount=loan_in.principal_amount,
        repayment_frequency=loan_in.repayment_frequency,
        periodic_interest_rate=periodic_interest_rate,
        term_length=loan_in.term_length,
        start_date=loan_in.start_date,
        end_date=end_date,
        status=loan_in.status,
        grace_period_days=loan_in.grace_period_days,
        notes=loan_in.notes,
    )

    db.add(loan)
    db.flush()
    schedule_items = build_schedule_items(loan)
    db.add_all(schedule_items)
    db.commit()
    db.refresh(loan)
    return loan
