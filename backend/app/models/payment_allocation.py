"""Payment allocation ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PaymentAllocation(Base):
    """Allocation of a payment across one specific obligation."""

    __tablename__ = "payment_allocations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_allocations_amount_positive"),
        CheckConstraint(
            """
            allocation_type IN (
                'late_charge_interest',
                'late_charge_principal',
                'regular_interest',
                'regular_principal'
            )
            """,
            name="ck_payment_allocations_allocation_type",
        ),
        CheckConstraint(
            """
            (schedule_item_id IS NOT NULL AND late_charge_id IS NULL)
            OR
            (schedule_item_id IS NULL AND late_charge_id IS NOT NULL)
            """,
            name="ck_payment_allocations_exactly_one_target",
        ),
        Index("idx_payment_allocations_payment_id", "payment_id"),
        Index("idx_payment_allocations_loan_id", "loan_id"),
        Index("idx_payment_allocations_schedule_item_id", "schedule_item_id"),
        Index("idx_payment_allocations_late_charge_id", "late_charge_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
    )
    schedule_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repayment_schedule_items.id", ondelete="CASCADE"),
    )
    late_charge_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("late_charges.id", ondelete="CASCADE"),
    )
    allocation_type: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    payment: Mapped["Payment"] = relationship("Payment", back_populates="allocations")
    loan: Mapped["Loan"] = relationship("Loan", back_populates="payment_allocations")
    schedule_item: Mapped["RepaymentScheduleItem | None"] = relationship(
        "RepaymentScheduleItem",
        back_populates="payment_allocations",
    )
    late_charge: Mapped["LateCharge | None"] = relationship(
        "LateCharge",
        back_populates="payment_allocations",
    )
