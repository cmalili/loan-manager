"""Reporting and read-side query service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.borrower import Borrower
from app.models.loan import Loan
from app.models.payment import Payment
from app.services.borrower import get_borrower
from app.services.money import ZERO, quantize_money
from app.services.overdue import (
    late_charge_interest_outstanding,
    late_charge_principal_outstanding,
    process_overdue_loans,
    total_regular_outstanding,
)


@dataclass(slots=True)
class OverdueLoanSummary:
    """Report row for one overdue loan."""

    loan_id: object
    borrower_id: object
    borrower_name: str
    loan_status: str
    earliest_overdue_due_date: date
    days_overdue: int
    overdue_installment_count: int
    overdue_regular_balance: Decimal
    outstanding_late_charge_balance: Decimal
    total_overdue_balance: Decimal


def list_borrower_loan_history(db: Session, borrower_id):
    """Return all loans for one borrower in reverse chronological order."""

    get_borrower(db, borrower_id)
    statement = (
        select(Loan)
        .where(Loan.borrower_id == borrower_id)
        .order_by(Loan.created_at.desc(), Loan.start_date.desc())
    )
    return list(db.scalars(statement).all())


def build_overdue_loan_summary(loan: Loan, *, as_of_date: date) -> OverdueLoanSummary:
    """Build the overdue summary row for one loan."""

    overdue_items = [item for item in loan.schedule_items if item.status == "overdue"]
    earliest_due_date = min(item.due_date for item in overdue_items)
    overdue_regular_balance = quantize_money(
        sum((total_regular_outstanding(item) for item in overdue_items), ZERO)
    )
    outstanding_late_charge_balance = quantize_money(
        sum(
            (
                late_charge_interest_outstanding(charge)
                + late_charge_principal_outstanding(charge)
                for charge in loan.late_charges
                if charge.status != "voided"
            ),
            ZERO,
        )
    )
    total_overdue_balance = quantize_money(
        overdue_regular_balance + outstanding_late_charge_balance
    )
    return OverdueLoanSummary(
        loan_id=loan.id,
        borrower_id=loan.borrower_id,
        borrower_name=loan.borrower.full_name,
        loan_status=loan.status,
        earliest_overdue_due_date=earliest_due_date,
        days_overdue=(as_of_date - earliest_due_date).days,
        overdue_installment_count=len(overdue_items),
        overdue_regular_balance=overdue_regular_balance,
        outstanding_late_charge_balance=outstanding_late_charge_balance,
        total_overdue_balance=total_overdue_balance,
    )


def list_overdue_loans(
    db: Session,
    *,
    as_of_date: date,
    acting_user_id: UUID | None = None,
) -> list[OverdueLoanSummary]:
    """Return overdue loans using the same source-of-truth delinquency logic."""

    process_overdue_loans(
        db,
        as_of_date=as_of_date,
        created_by_user_id=acting_user_id,
    )
    statement = (
        select(Loan)
        .where(Loan.status == "overdue")
        .options(
            selectinload(Loan.borrower),
            selectinload(Loan.schedule_items),
            selectinload(Loan.late_charges),
        )
        .order_by(Loan.start_date.asc(), Loan.created_at.asc())
    )
    loans = list(db.scalars(statement).all())
    return [build_overdue_loan_summary(loan, as_of_date=as_of_date) for loan in loans]


def list_recent_payments(db: Session, *, limit: int = 20) -> list[Payment]:
    """Return recent recorded payments ordered newest first."""

    statement = (
        select(Payment)
        .where(Payment.status == "recorded")
        .options(selectinload(Payment.allocations))
        .order_by(Payment.payment_date.desc(), Payment.recorded_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def _calculate_total_outstanding_balance(loans: list[Loan]) -> Decimal:
    total = ZERO
    for loan in loans:
        for item in loan.schedule_items:
            total += total_regular_outstanding(item)
        for charge in loan.late_charges:
            if charge.status == "voided":
                continue
            total += late_charge_interest_outstanding(charge)
            total += late_charge_principal_outstanding(charge)
    return quantize_money(total)


def get_dashboard_summary(
    db: Session,
    *,
    as_of_date: date,
    recent_days: int = 7,
    acting_user_id: UUID | None = None,
) -> dict[str, object]:
    """Return dashboard metrics derived from source-of-truth rows."""

    overdue_rows = list_overdue_loans(
        db,
        as_of_date=as_of_date,
        acting_user_id=acting_user_id,
    )
    statement = (
        select(Loan)
        .where(Loan.status.in_(("active", "closed", "overdue")))
        .options(selectinload(Loan.schedule_items), selectinload(Loan.late_charges))
    )
    loans = list(db.scalars(statement).all())
    recent_cutoff = as_of_date - timedelta(days=recent_days - 1)
    recent_payments_statement = select(Payment).where(
        Payment.status == "recorded",
        Payment.payment_date >= recent_cutoff,
        Payment.payment_date <= as_of_date,
    )
    recent_payments = list(db.scalars(recent_payments_statement).all())

    return {
        "active_loan_count": sum(1 for loan in loans if loan.status == "active"),
        "closed_loan_count": sum(1 for loan in loans if loan.status == "closed"),
        "overdue_loan_count": len(overdue_rows),
        "total_outstanding_balance": _calculate_total_outstanding_balance(loans),
        "total_overdue_balance": quantize_money(
            sum(
                (row.total_overdue_balance for row in overdue_rows),
                ZERO,
            )
        ),
        "recent_payment_count": len(recent_payments),
        "recent_payment_total": quantize_money(
            sum((payment.amount for payment in recent_payments), ZERO)
        ),
    }
