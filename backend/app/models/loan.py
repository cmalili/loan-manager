"""Loan ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Loan(Base):
    """Loan issued to a borrower."""

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="ck_loans_principal_amount_positive"),
        CheckConstraint(
            "repayment_frequency IN ('weekly', 'monthly')",
            name="ck_loans_repayment_frequency",
        ),
        CheckConstraint("periodic_interest_rate >= 0", name="ck_loans_periodic_interest_rate_nonnegative"),
        CheckConstraint("term_length > 0", name="ck_loans_term_length_positive"),
        CheckConstraint(
            "status IN ('draft', 'active', 'closed', 'overdue', 'defaulted', 'restructured', 'cancelled')",
            name="ck_loans_status",
        ),
        CheckConstraint("grace_period_days >= 0", name="ck_loans_grace_period_days_nonnegative"),
        CheckConstraint("end_date >= start_date", name="ck_loans_end_date_after_start_date"),
        Index("idx_loans_borrower_id", "borrower_id"),
        Index("idx_loans_status", "status"),
        Index("idx_loans_start_date", "start_date"),
        Index("idx_loans_end_date", "end_date"),
        Index(
            "uq_loans_one_active_per_borrower",
            "borrower_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    repayment_frequency: Mapped[str] = mapped_column(Text, nullable=False)
    periodic_interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    term_length: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    grace_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        server_default=text("7"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    borrower: Mapped["Borrower"] = relationship("Borrower", back_populates="loans")
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="created_loans",
        foreign_keys=[created_by_user_id],
    )
    schedule_items: Mapped[list["RepaymentScheduleItem"]] = relationship(
        "RepaymentScheduleItem",
        back_populates="loan",
        cascade="all, delete-orphan",
    )
    late_charges: Mapped[list["LateCharge"]] = relationship(
        "LateCharge",
        back_populates="loan",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="loan")
    payment_allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="loan",
        cascade="all, delete-orphan",
    )
