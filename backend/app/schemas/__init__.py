"""Validation schemas package."""
"""API schemas package."""

from app.schemas.borrower import BorrowerCreate, BorrowerRead, BorrowerUpdate
from app.schemas.loan import LoanCreate, LoanRead
from app.schemas.payment import PaymentCreate, PaymentRead
from app.schemas.reporting import (
    BorrowerLoanHistoryItem,
    DashboardSummaryRead,
    OverdueLoanRead,
    RecentPaymentRead,
)

__all__ = [
    "BorrowerCreate",
    "BorrowerRead",
    "BorrowerUpdate",
    "BorrowerLoanHistoryItem",
    "DashboardSummaryRead",
    "LoanCreate",
    "LoanRead",
    "OverdueLoanRead",
    "PaymentCreate",
    "PaymentRead",
    "RecentPaymentRead",
]
