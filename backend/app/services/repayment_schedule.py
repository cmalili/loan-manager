"""Repayment schedule generation service."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.models.loan import Loan
from app.models.repayment_schedule_item import RepaymentScheduleItem


TWOPLACES = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


@dataclass(slots=True)
class ScheduleInstallment:
    """In-memory representation of one generated installment."""

    installment_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    status: str = "pending"


def quantize_money(value: Decimal) -> Decimal:
    """Round money values to two decimal places using a stable rule."""

    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def add_months(value: date, months: int) -> date:
    """Add calendar months while clamping to the target month length."""

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def next_due_date(start_date: date, repayment_frequency: str, installment_number: int) -> date:
    """Return the due date for a given installment number."""

    if repayment_frequency == "weekly":
        return start_date + timedelta(weeks=installment_number)
    if repayment_frequency == "monthly":
        return add_months(start_date, installment_number)
    raise ValueError(f"Unsupported repayment frequency: {repayment_frequency}")


def build_repayment_schedule(loan: Loan) -> list[ScheduleInstallment]:
    """Generate a repayment schedule from a loan's core financial terms."""

    periodic_rate = loan.periodic_interest_rate / ONE_HUNDRED
    base_principal_installment = quantize_money(loan.principal_amount / loan.term_length)
    remaining_principal = loan.principal_amount
    installments: list[ScheduleInstallment] = []

    for installment_number in range(1, loan.term_length + 1):
        if installment_number == loan.term_length:
            principal_due = quantize_money(remaining_principal)
        else:
            principal_due = base_principal_installment

        interest_due = quantize_money(remaining_principal * periodic_rate)
        due_date = next_due_date(loan.start_date, loan.repayment_frequency, installment_number)

        installments.append(
            ScheduleInstallment(
                installment_number=installment_number,
                due_date=due_date,
                principal_due=principal_due,
                interest_due=interest_due,
            )
        )

        remaining_principal = quantize_money(remaining_principal - principal_due)

    return installments


def build_schedule_items(loan: Loan) -> list[RepaymentScheduleItem]:
    """Create ORM schedule items ready to persist for the given loan."""

    return [
        RepaymentScheduleItem(
            loan_id=loan.id,
            installment_number=installment.installment_number,
            due_date=installment.due_date,
            principal_due=installment.principal_due,
            interest_due=installment.interest_due,
            status=installment.status,
        )
        for installment in build_repayment_schedule(loan)
    ]
