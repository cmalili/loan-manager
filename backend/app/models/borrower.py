"""Borrower ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Borrower(Base):
    """Borrower record."""

    __tablename__ = "borrowers"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name="ck_borrowers_status"),
        Index("idx_borrowers_full_name", "full_name"),
        Index("idx_borrowers_phone_number", "phone_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(Text)
    external_id_number: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    loans: Mapped[list["Loan"]] = relationship("Loan", back_populates="borrower")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="borrower")
