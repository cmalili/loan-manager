"""Late charge ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class LateCharge(Base):
    """Late charge created after an installment passes the grace period."""

    __tablename__ = "late_charges"
    __table_args__ = (
        CheckConstraint("base_unpaid_amount >= 0", name="ck_late_charges_base_unpaid_amount_nonnegative"),
        CheckConstraint("charge_rate >= 0", name="ck_late_charges_charge_rate_nonnegative"),
        CheckConstraint(
            "charge_principal_amount >= 0",
            name="ck_late_charges_charge_principal_amount_nonnegative",
        ),
        CheckConstraint(
            "accrued_interest_amount >= 0",
            name="ck_late_charges_accrued_interest_amount_nonnegative",
        ),
        CheckConstraint("principal_paid >= 0", name="ck_late_charges_principal_paid_nonnegative"),
        CheckConstraint("interest_paid >= 0", name="ck_late_charges_interest_paid_nonnegative"),
        CheckConstraint("waived_amount >= 0", name="ck_late_charges_waived_amount_nonnegative"),
        CheckConstraint(
            "interest_periods_accrued >= 0",
            name="ck_late_charges_interest_periods_accrued_nonnegative",
        ),
        CheckConstraint(
            "status IN ('outstanding', 'partially_paid', 'paid', 'waived', 'voided')",
            name="ck_late_charges_status",
        ),
        UniqueConstraint("schedule_item_id", name="uq_late_charges_schedule_item_id"),
        Index("idx_late_charges_loan_id", "loan_id"),
        Index("idx_late_charges_status", "status"),
        Index("idx_late_charges_trigger_date", "trigger_date"),
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
    schedule_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repayment_schedule_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    trigger_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_unpaid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    charge_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    charge_principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accrued_interest_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    principal_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    interest_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    waived_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    interest_periods_accrued: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    loan: Mapped["Loan"] = relationship("Loan", back_populates="late_charges")
    schedule_item: Mapped["RepaymentScheduleItem"] = relationship(
        "RepaymentScheduleItem",
        back_populates="late_charge",
    )
    created_by_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_late_charges",
        foreign_keys=[created_by_user_id],
    )
    payment_allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="late_charge",
    )
