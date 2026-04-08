"""Repayment schedule item ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class RepaymentScheduleItem(Base):
    """Single installment for a loan."""

    __tablename__ = "repayment_schedule_items"
    __table_args__ = (
        CheckConstraint("installment_number > 0", name="ck_schedule_items_installment_number_positive"),
        CheckConstraint("principal_due >= 0", name="ck_schedule_items_principal_due_nonnegative"),
        CheckConstraint("interest_due >= 0", name="ck_schedule_items_interest_due_nonnegative"),
        CheckConstraint("principal_paid >= 0", name="ck_schedule_items_principal_paid_nonnegative"),
        CheckConstraint("interest_paid >= 0", name="ck_schedule_items_interest_paid_nonnegative"),
        CheckConstraint("waived_amount >= 0", name="ck_schedule_items_waived_amount_nonnegative"),
        CheckConstraint(
            "status IN ('pending', 'partially_paid', 'paid', 'overdue', 'waived')",
            name="ck_schedule_items_status",
        ),
        UniqueConstraint("loan_id", "installment_number", name="uq_schedule_items_loan_installment"),
        Index("idx_schedule_items_loan_id", "loan_id"),
        Index("idx_schedule_items_due_date", "due_date"),
        Index("idx_schedule_items_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interest_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    principal_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    interest_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    waived_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    loan: Mapped["Loan"] = relationship("Loan", back_populates="schedule_items")
    late_charge: Mapped["LateCharge | None"] = relationship(
        "LateCharge",
        back_populates="schedule_item",
        uselist=False,
    )
    payment_allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="schedule_item",
    )
