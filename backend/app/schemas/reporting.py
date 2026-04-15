"""Schemas for reporting and read-side query views."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.loan import LoanRead
from app.schemas.payment import PaymentRead


class BorrowerLoanHistoryItem(LoanRead):
    """Loan history item for a borrower."""


class OverdueLoanRead(BaseModel):
    """Loan plus overdue metrics for overdue reporting."""

    model_config = ConfigDict(from_attributes=True)

    loan_id: UUID
    borrower_id: UUID
    borrower_name: str
    loan_status: str
    earliest_overdue_due_date: date
    days_overdue: int
    overdue_installment_count: int
    overdue_regular_balance: Decimal
    outstanding_late_charge_balance: Decimal
    total_overdue_balance: Decimal


class RecentPaymentRead(PaymentRead):
    """Recent payment row for reporting."""


class DashboardSummaryRead(BaseModel):
    """Dashboard summary values derived from source-of-truth records."""

    active_loan_count: int
    closed_loan_count: int
    overdue_loan_count: int
    total_outstanding_balance: Decimal
    total_overdue_balance: Decimal
    recent_payment_count: int
    recent_payment_total: Decimal
