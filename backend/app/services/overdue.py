"""Overdue detection and late-charge processing service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.late_charge import LateCharge
from app.models.loan import Loan
from app.models.repayment_schedule_item import RepaymentScheduleItem
from app.services.audit import record_audit_log, snapshot_model
from app.services.money import ONE_HUNDRED, ZERO, quantize_money
from app.services.repayment_schedule import add_months


LATE_CHARGE_RATE = Decimal("10.00")


@dataclass(slots=True)
class OverdueProcessingResult:
    """Summary of the overdue-processing pass."""

    loans_processed: int = 0
    schedule_items_marked_overdue: int = 0
    late_charges_created: int = 0
    late_charges_accrued: int = 0


def regular_interest_outstanding(item: RepaymentScheduleItem) -> Decimal:
    """Return unpaid regular interest for one schedule item."""

    return quantize_money(item.interest_due - item.interest_paid)


def regular_principal_outstanding(item: RepaymentScheduleItem) -> Decimal:
    """Return unpaid regular principal for one schedule item."""

    return quantize_money(item.principal_due - item.principal_paid - item.waived_amount)


def total_regular_outstanding(item: RepaymentScheduleItem) -> Decimal:
    """Return the unpaid regular balance for one schedule item."""

    return quantize_money(
        regular_interest_outstanding(item) + regular_principal_outstanding(item)
    )


def late_charge_interest_outstanding(charge: LateCharge) -> Decimal:
    """Return unpaid accrued interest for one late charge."""

    return quantize_money(charge.accrued_interest_amount - charge.interest_paid)


def late_charge_principal_outstanding(charge: LateCharge) -> Decimal:
    """Return unpaid late-charge principal for one late charge."""

    return quantize_money(
        charge.charge_principal_amount - charge.principal_paid - charge.waived_amount
    )


def is_schedule_item_overdue(
    item: RepaymentScheduleItem,
    *,
    as_of_date: date,
    grace_period_days: int,
) -> bool:
    """Return whether the schedule item is overdue as of the supplied date."""

    if total_regular_outstanding(item) <= ZERO:
        return False
    overdue_trigger_date = item.due_date + timedelta(days=grace_period_days)
    return as_of_date > overdue_trigger_date


def sync_schedule_item_status(
    item: RepaymentScheduleItem,
    *,
    as_of_date: date,
    grace_period_days: int,
) -> bool:
    """Update a schedule item status from its balances and timing rules."""

    previous_status = item.status
    outstanding_balance = total_regular_outstanding(item)

    if outstanding_balance == ZERO:
        if (
            item.waived_amount > ZERO
            and item.principal_paid == ZERO
            and item.interest_paid == ZERO
        ):
            item.status = "waived"
        else:
            item.status = "paid"
    elif is_schedule_item_overdue(
        item,
        as_of_date=as_of_date,
        grace_period_days=grace_period_days,
    ):
        item.status = "overdue"
    elif (
        item.principal_paid > ZERO
        or item.interest_paid > ZERO
        or item.waived_amount > ZERO
    ):
        item.status = "partially_paid"
    else:
        item.status = "pending"

    return previous_status != item.status


def sync_late_charge_status(charge: LateCharge) -> None:
    """Update a late-charge status from its balances."""

    interest_outstanding = late_charge_interest_outstanding(charge)
    principal_outstanding = late_charge_principal_outstanding(charge)

    if interest_outstanding == ZERO and principal_outstanding == ZERO:
        if (
            charge.waived_amount > ZERO
            and charge.principal_paid == ZERO
            and charge.interest_paid == ZERO
        ):
            charge.status = "waived"
        else:
            charge.status = "paid"
    elif (
        charge.principal_paid > ZERO
        or charge.interest_paid > ZERO
        or charge.waived_amount > ZERO
    ):
        charge.status = "partially_paid"
    else:
        charge.status = "outstanding"


def completed_periods_since(
    start_date: date,
    *,
    as_of_date: date,
    repayment_frequency: str,
) -> int:
    """Return the number of fully completed interest periods since a start date."""

    if as_of_date <= start_date:
        return 0

    if repayment_frequency == "weekly":
        return (as_of_date - start_date).days // 7

    if repayment_frequency == "monthly":
        periods = 0
        while add_months(start_date, periods + 1) <= as_of_date:
            periods += 1
        return periods

    raise ValueError(f"Unsupported repayment frequency: {repayment_frequency}")


def accrue_late_charge_interest(
    charge: LateCharge,
    *,
    loan: Loan,
    as_of_date: date,
) -> bool:
    """Accrue periodic interest on a late charge through the supplied date."""

    sync_late_charge_status(charge)
    if charge.status in {"paid", "waived", "voided"}:
        return False

    target_periods = completed_periods_since(
        charge.trigger_date,
        as_of_date=as_of_date,
        repayment_frequency=loan.repayment_frequency,
    )
    new_periods = target_periods - charge.interest_periods_accrued
    if new_periods <= 0:
        return False

    principal_base = late_charge_principal_outstanding(charge)
    if principal_base <= ZERO:
        charge.interest_periods_accrued = target_periods
        sync_late_charge_status(charge)
        return False

    periodic_rate = loan.periodic_interest_rate / ONE_HUNDRED
    accrued_increment = quantize_money(principal_base * periodic_rate * new_periods)
    charge.accrued_interest_amount = quantize_money(
        charge.accrued_interest_amount + accrued_increment
    )
    charge.interest_periods_accrued = target_periods
    sync_late_charge_status(charge)
    return accrued_increment > ZERO


def create_late_charge_for_item(
    item: RepaymentScheduleItem,
    *,
    loan: Loan,
    created_by_user_id: UUID | None,
) -> LateCharge | None:
    """Create the one-time late charge for an overdue schedule item."""

    if item.late_charge is not None:
        return None

    base_unpaid_amount = total_regular_outstanding(item)
    if base_unpaid_amount <= ZERO:
        return None

    trigger_date = item.due_date + timedelta(days=loan.grace_period_days)
    return LateCharge(
        loan_id=loan.id,
        schedule_item_id=item.id,
        created_by_user_id=created_by_user_id,
        trigger_date=trigger_date,
        base_unpaid_amount=base_unpaid_amount,
        charge_rate=LATE_CHARGE_RATE,
        charge_principal_amount=quantize_money(
            base_unpaid_amount * LATE_CHARGE_RATE / ONE_HUNDRED
        ),
        accrued_interest_amount=ZERO,
        principal_paid=ZERO,
        interest_paid=ZERO,
        waived_amount=ZERO,
        interest_periods_accrued=0,
        status="outstanding",
    )


def list_loans_for_overdue_processing(db: Session) -> list[Loan]:
    """Return loans whose operational status may change during delinquency processing."""

    statement = select(Loan).where(Loan.status.in_(("active", "overdue", "closed")))
    return list(db.scalars(statement).all())


def list_schedule_items_for_loan(db: Session, loan_id) -> list[RepaymentScheduleItem]:
    """Return schedule items ordered by installment number."""

    statement = select(RepaymentScheduleItem).where(
        RepaymentScheduleItem.loan_id == loan_id
    ).order_by(RepaymentScheduleItem.installment_number.asc())
    return list(db.scalars(statement).all())


def list_late_charges_for_loan(db: Session, loan_id) -> list[LateCharge]:
    """Return non-voided late charges ordered by trigger time."""

    statement = select(LateCharge).where(
        LateCharge.loan_id == loan_id,
        LateCharge.status != "voided",
    ).order_by(LateCharge.trigger_date.asc(), LateCharge.created_at.asc())
    return list(db.scalars(statement).all())


def sync_loan_status(
    db: Session,
    loan: Loan,
    *,
    schedule_items: list[RepaymentScheduleItem],
    late_charges: list[LateCharge],
    acting_user_id: UUID | None,
) -> None:
    """Update the loan status from current balances and delinquency state."""

    previous_status = loan.status
    regular_outstanding = sum(
        (total_regular_outstanding(item) for item in schedule_items),
        ZERO,
    )
    late_charge_outstanding = sum(
        (
            late_charge_interest_outstanding(charge)
            + late_charge_principal_outstanding(charge)
            for charge in late_charges
            if charge.status != "voided"
        ),
        ZERO,
    )
    total_outstanding = quantize_money(regular_outstanding + late_charge_outstanding)

    if total_outstanding == ZERO:
        loan.status = "closed"
    else:
        has_overdue_item = any(item.status == "overdue" for item in schedule_items)
        if has_overdue_item:
            loan.status = "overdue"
        elif loan.status in {"active", "overdue", "closed"}:
            loan.status = "active"

    if previous_status != loan.status:
        record_audit_log(
            db,
            user_id=acting_user_id,
            entity_type="loan",
            entity_id=loan.id,
            action_type="status_change",
            before_state={"status": previous_status},
            after_state={"status": loan.status},
        )


def process_loan_overdue_state(
    db: Session,
    loan: Loan,
    *,
    as_of_date: date,
    created_by_user_id: UUID | None = None,
) -> OverdueProcessingResult:
    """Refresh overdue state, late charges, and loan status for one loan."""

    result = OverdueProcessingResult(loans_processed=1)
    schedule_items = list_schedule_items_for_loan(db, loan.id)

    for item in schedule_items:
        previous_status = item.status
        sync_schedule_item_status(
            item,
            as_of_date=as_of_date,
            grace_period_days=loan.grace_period_days,
        )
        if previous_status != "overdue" and item.status == "overdue":
            result.schedule_items_marked_overdue += 1

        if (
            item.status == "overdue"
            and item.late_charge is None
            and as_of_date > item.due_date + timedelta(days=loan.grace_period_days)
        ):
            late_charge = create_late_charge_for_item(
                item,
                loan=loan,
                created_by_user_id=created_by_user_id,
            )
            if late_charge is not None:
                db.add(late_charge)
                db.flush()
                item.late_charge = late_charge
                record_audit_log(
                    db,
                    user_id=created_by_user_id,
                    entity_type="late_charge",
                    entity_id=late_charge.id,
                    action_type="create",
                    before_state=None,
                    after_state=snapshot_model(late_charge),
                )
                result.late_charges_created += 1

    late_charges = list_late_charges_for_loan(db, loan.id)
    for charge in late_charges:
        before_state = snapshot_model(charge)
        if accrue_late_charge_interest(charge, loan=loan, as_of_date=as_of_date):
            record_audit_log(
                db,
                user_id=created_by_user_id,
                entity_type="late_charge",
                entity_id=charge.id,
                action_type="interest_accrual",
                before_state=before_state,
                after_state=snapshot_model(charge),
            )
            result.late_charges_accrued += 1
        sync_late_charge_status(charge)

    sync_loan_status(
        db,
        loan,
        schedule_items=schedule_items,
        late_charges=late_charges,
        acting_user_id=created_by_user_id,
    )
    return result


def process_overdue_loans(
    db: Session,
    *,
    as_of_date: date,
    created_by_user_id: UUID | None = None,
) -> OverdueProcessingResult:
    """Refresh overdue state for all loans that participate in repayment workflows."""

    total_result = OverdueProcessingResult()
    for loan in list_loans_for_overdue_processing(db):
        loan_result = process_loan_overdue_state(
            db,
            loan,
            as_of_date=as_of_date,
            created_by_user_id=created_by_user_id,
        )
        total_result.loans_processed += loan_result.loans_processed
        total_result.schedule_items_marked_overdue += (
            loan_result.schedule_items_marked_overdue
        )
        total_result.late_charges_created += loan_result.late_charges_created
        total_result.late_charges_accrued += loan_result.late_charges_accrued

    db.commit()
    return total_result
