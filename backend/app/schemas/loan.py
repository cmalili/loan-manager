"""Pydantic schemas for loan API input and output."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RepaymentFrequency = Literal["weekly", "monthly"]
LoanStatus = Literal[
    "draft",
    "active",
    "closed",
    "overdue",
    "defaulted",
    "restructured",
    "cancelled",
]
LoanCreateStatus = Literal["draft", "active"]


class LoanCreate(BaseModel):
    """Payload for creating a loan."""

    borrower_id: UUID
    created_by_user_id: UUID
    principal_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    repayment_frequency: RepaymentFrequency
    term_length: int = Field(gt=0)
    start_date: date
    status: LoanCreateStatus = "draft"
    grace_period_days: int = Field(default=7, ge=0)
    notes: str | None = None


class LoanRead(BaseModel):
    """Loan response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    borrower_id: UUID
    created_by_user_id: UUID
    principal_amount: Decimal
    repayment_frequency: RepaymentFrequency
    periodic_interest_rate: Decimal
    term_length: int
    start_date: date
    end_date: date
    status: LoanStatus
    grace_period_days: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
