"""Validation schemas package."""
"""API schemas package."""

from app.schemas.auth import AuthenticatedUserRead, LoginRequest, LoginResponse
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
    "AuthenticatedUserRead",
    "BorrowerCreate",
    "BorrowerRead",
    "BorrowerUpdate",
    "BorrowerLoanHistoryItem",
    "DashboardSummaryRead",
    "LoanCreate",
    "LoanRead",
    "LoginRequest",
    "LoginResponse",
    "OverdueLoanRead",
    "PaymentCreate",
    "PaymentRead",
    "RecentPaymentRead",
]
