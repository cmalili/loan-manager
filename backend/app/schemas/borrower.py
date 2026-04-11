"""Pydantic schemas for borrower API input and output."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


BorrowerStatus = Literal["active", "inactive"]


class BorrowerBase(BaseModel):
    """Shared borrower fields."""

    full_name: str = Field(min_length=1)
    phone_number: str | None = None
    external_id_number: str | None = None
    address: str | None = None
    notes: str | None = None
    status: BorrowerStatus = "active"


class BorrowerCreate(BorrowerBase):
    """Payload for creating a borrower."""


class BorrowerUpdate(BaseModel):
    """Payload for partially updating a borrower."""

    full_name: str | None = Field(default=None, min_length=1)
    phone_number: str | None = None
    external_id_number: str | None = None
    address: str | None = None
    notes: str | None = None
    status: BorrowerStatus | None = None


class BorrowerRead(BorrowerBase):
    """Borrower response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
