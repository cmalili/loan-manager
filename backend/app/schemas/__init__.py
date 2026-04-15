"""Validation schemas package."""
"""API schemas package."""

from app.schemas.borrower import BorrowerCreate, BorrowerRead, BorrowerUpdate
from app.schemas.loan import LoanCreate, LoanRead
from app.schemas.payment import PaymentCreate, PaymentRead

__all__ = [
    "BorrowerCreate",
    "BorrowerRead",
    "BorrowerUpdate",
    "LoanCreate",
    "LoanRead",
    "PaymentCreate",
    "PaymentRead",
]
