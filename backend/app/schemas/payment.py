"""Pydantic schemas for payment API input and output."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


PaymentStatus = Literal["recorded", "voided", "reversed"]
PaymentAllocationType = Literal[
    "late_charge_interest",
    "late_charge_principal",
    "regular_interest",
    "regular_principal",
]


class PaymentCreate(BaseModel):
    """Payload for recording a payment."""

    loan_id: UUID
    borrower_id: UUID
    recorded_by_user_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_date: date
    payment_method: str | None = None
    reference_code: str | None = None
    notes: str | None = None


class PaymentAllocationRead(BaseModel):
    """Payment allocation response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: UUID
    loan_id: UUID
    schedule_item_id: UUID | None
    late_charge_id: UUID | None
    allocation_type: PaymentAllocationType
    amount: Decimal
    created_at: datetime


class PaymentRead(BaseModel):
    """Payment response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loan_id: UUID
    borrower_id: UUID
    recorded_by_user_id: UUID
    amount: Decimal
    payment_date: date
    recorded_at: datetime
    payment_method: str | None
    reference_code: str | None
    notes: str | None
    is_backdated: bool
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    allocations: list[PaymentAllocationRead]
