"""Payment service layer."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.models.late_charge import LateCharge
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.models.repayment_schedule_item import RepaymentScheduleItem
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.services.audit import record_audit_log, snapshot_model
from app.services.money import ZERO, quantize_money
from app.services.overdue import process_loan_overdue_state


class PaymentValidationError(ValueError):
    """Raised when a payment violates business rules."""


class PaymentLoanNotFoundError(LookupError):
    """Raised when a payment references a missing loan."""


class PaymentBorrowerNotFoundError(LookupError):
    """Raised when a payment references a missing borrower."""


class PaymentRecorderNotFoundError(LookupError):
    """Raised when a payment references a missing user."""


class BackdatedPaymentNotAllowedError(ValueError):
    """Raised when a non-admin user attempts to record a backdated payment."""


def _money(value: Decimal) -> Decimal:
    return quantize_money(value)


def list_schedule_items_for_loan(db: Session, loan_id) -> list[RepaymentScheduleItem]:
    statement = select(RepaymentScheduleItem).where(
        RepaymentScheduleItem.loan_id == loan_id
    ).order_by(RepaymentScheduleItem.installment_number.asc())
    return list(db.scalars(statement).all())


def list_late_charges_for_loan(db: Session, loan_id) -> list[LateCharge]:
    statement = select(LateCharge).where(
        LateCharge.loan_id == loan_id,
        LateCharge.status != "voided",
    ).order_by(LateCharge.trigger_date.asc(), LateCharge.created_at.asc())
    return list(db.scalars(statement).all())


def schedule_item_regular_interest_outstanding(item: RepaymentScheduleItem) -> Decimal:
    return _money(item.interest_due - item.interest_paid)


def schedule_item_regular_principal_outstanding(item: RepaymentScheduleItem) -> Decimal:
    return _money(item.principal_due - item.principal_paid - item.waived_amount)


def late_charge_interest_outstanding(charge: LateCharge) -> Decimal:
    return _money(charge.accrued_interest_amount - charge.interest_paid)


def late_charge_principal_outstanding(charge: LateCharge) -> Decimal:
    return _money(
        charge.charge_principal_amount - charge.principal_paid - charge.waived_amount
    )


def total_outstanding_balance(
    schedule_items: list[RepaymentScheduleItem],
    late_charges: list[LateCharge],
) -> Decimal:
    total = ZERO
    for charge in late_charges:
        total += late_charge_interest_outstanding(charge)
        total += late_charge_principal_outstanding(charge)
    for item in schedule_items:
        total += schedule_item_regular_interest_outstanding(item)
        total += schedule_item_regular_principal_outstanding(item)
    return _money(total)


def _apply_to_late_charge_component(
    payment: Payment,
    late_charges: list[LateCharge],
    amount_remaining: Decimal,
    *,
    allocation_type: str,
    paid_field: str,
    outstanding_calculator: Callable[[LateCharge], Decimal],
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    for charge in late_charges:
        if amount_remaining <= ZERO:
            break

        outstanding = outstanding_calculator(charge)
        if outstanding <= ZERO:
            continue

        amount_to_apply = min(amount_remaining, outstanding)
        setattr(
            charge,
            paid_field,
            _money(getattr(charge, paid_field) + amount_to_apply),
        )
        allocations.append(
            PaymentAllocation(
                payment_id=payment.id,
                loan_id=payment.loan_id,
                late_charge_id=charge.id,
                allocation_type=allocation_type,
                amount=amount_to_apply,
            )
        )
        amount_remaining = _money(amount_remaining - amount_to_apply)

    return allocations, amount_remaining


def _sync_late_charge_status_after_payment(charge: LateCharge) -> None:
    if (
        late_charge_interest_outstanding(charge) == ZERO
        and late_charge_principal_outstanding(charge) == ZERO
    ):
        charge.status = "paid"
    elif (
        charge.interest_paid > ZERO
        or charge.principal_paid > ZERO
        or charge.waived_amount > ZERO
    ):
        charge.status = "partially_paid"


def apply_payment_to_late_charges(
    payment: Payment,
    late_charges: list[LateCharge],
    amount_remaining: Decimal,
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    interest_allocations, amount_remaining = _apply_to_late_charge_component(
        payment,
        late_charges,
        amount_remaining,
        allocation_type="late_charge_interest",
        paid_field="interest_paid",
        outstanding_calculator=late_charge_interest_outstanding,
    )
    allocations.extend(interest_allocations)

    principal_allocations, amount_remaining = _apply_to_late_charge_component(
        payment,
        late_charges,
        amount_remaining,
        allocation_type="late_charge_principal",
        paid_field="principal_paid",
        outstanding_calculator=late_charge_principal_outstanding,
    )
    allocations.extend(principal_allocations)

    for charge in late_charges:
        _sync_late_charge_status_after_payment(charge)

    return allocations, amount_remaining


def _apply_to_schedule_item_component(
    payment: Payment,
    schedule_items: list[RepaymentScheduleItem],
    amount_remaining: Decimal,
    *,
    allocation_type: str,
    paid_field: str,
    outstanding_calculator: Callable[[RepaymentScheduleItem], Decimal],
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    for item in schedule_items:
        if amount_remaining <= ZERO:
            break

        outstanding = outstanding_calculator(item)
        if outstanding <= ZERO:
            continue

        amount_to_apply = min(amount_remaining, outstanding)
        setattr(
            item,
            paid_field,
            _money(getattr(item, paid_field) + amount_to_apply),
        )
        allocations.append(
            PaymentAllocation(
                payment_id=payment.id,
                loan_id=payment.loan_id,
                schedule_item_id=item.id,
                allocation_type=allocation_type,
                amount=amount_to_apply,
            )
        )
        amount_remaining = _money(amount_remaining - amount_to_apply)

    return allocations, amount_remaining


def _sync_schedule_item_status_after_payment(item: RepaymentScheduleItem) -> None:
    if (
        schedule_item_regular_interest_outstanding(item) == ZERO
        and schedule_item_regular_principal_outstanding(item) == ZERO
    ):
        item.status = "paid"
    elif (
        item.interest_paid > ZERO
        or item.principal_paid > ZERO
        or item.waived_amount > ZERO
    ):
        item.status = "partially_paid"


def apply_payment_to_schedule_items(
    payment: Payment,
    schedule_items: list[RepaymentScheduleItem],
    amount_remaining: Decimal,
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    interest_allocations, amount_remaining = _apply_to_schedule_item_component(
        payment,
        schedule_items,
        amount_remaining,
        allocation_type="regular_interest",
        paid_field="interest_paid",
        outstanding_calculator=schedule_item_regular_interest_outstanding,
    )
    allocations.extend(interest_allocations)

    principal_allocations, amount_remaining = _apply_to_schedule_item_component(
        payment,
        schedule_items,
        amount_remaining,
        allocation_type="regular_principal",
        paid_field="principal_paid",
        outstanding_calculator=schedule_item_regular_principal_outstanding,
    )
    allocations.extend(principal_allocations)

    for item in schedule_items:
        _sync_schedule_item_status_after_payment(item)

    return allocations, amount_remaining


def record_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    """Record a payment and allocate it across the loan obligations."""

    loan = db.get(Loan, payment_in.loan_id)
    if loan is None:
        raise PaymentLoanNotFoundError(f"Loan {payment_in.loan_id} was not found")

    if loan.status == "cancelled":
        raise PaymentValidationError("Cancelled loans do not accept payments")

    borrower = db.get(Borrower, payment_in.borrower_id)
    if borrower is None:
        raise PaymentBorrowerNotFoundError(f"Borrower {payment_in.borrower_id} was not found")

    recorder = db.get(User, payment_in.recorded_by_user_id)
    if recorder is None:
        raise PaymentRecorderNotFoundError(f"User {payment_in.recorded_by_user_id} was not found")

    today = date.today()
    if payment_in.payment_date < today and recorder.role != "admin":
        raise BackdatedPaymentNotAllowedError(
            "Only admin users may record backdated payments"
        )

    if loan.borrower_id != payment_in.borrower_id:
        raise PaymentValidationError("Payment borrower must match the loan borrower")

    process_loan_overdue_state(
        db,
        loan,
        as_of_date=payment_in.payment_date,
        created_by_user_id=payment_in.recorded_by_user_id,
    )

    schedule_items = list_schedule_items_for_loan(db, payment_in.loan_id)
    late_charges = list_late_charges_for_loan(db, payment_in.loan_id)
    outstanding_balance = total_outstanding_balance(schedule_items, late_charges)

    if payment_in.amount > outstanding_balance:
        raise PaymentValidationError(
            f"Payment amount {payment_in.amount} exceeds outstanding balance {outstanding_balance}"
        )

    payment = Payment(
        loan_id=payment_in.loan_id,
        borrower_id=payment_in.borrower_id,
        recorded_by_user_id=payment_in.recorded_by_user_id,
        amount=payment_in.amount,
        payment_date=payment_in.payment_date,
        payment_method=payment_in.payment_method,
        reference_code=payment_in.reference_code,
        notes=payment_in.notes,
        is_backdated=payment_in.payment_date < today,
        status="recorded",
    )

    db.add(payment)
    db.flush()

    amount_remaining = _money(payment.amount)
    late_charge_allocations, amount_remaining = apply_payment_to_late_charges(
        payment, late_charges, amount_remaining
    )
    schedule_allocations, amount_remaining = apply_payment_to_schedule_items(
        payment, schedule_items, amount_remaining
    )

    if amount_remaining != ZERO:
        raise PaymentValidationError(
            f"Payment allocation left an unexpected remainder of {amount_remaining}"
        )

    allocations = late_charge_allocations + schedule_allocations
    db.add_all(allocations)

    process_loan_overdue_state(
        db,
        loan,
        as_of_date=payment_in.payment_date,
        created_by_user_id=payment_in.recorded_by_user_id,
    )
    record_audit_log(
        db,
        user_id=payment.recorded_by_user_id,
        entity_type="payment",
        entity_id=payment.id,
        action_type="create",
        before_state=None,
        after_state=snapshot_model(payment),
    )

    db.commit()
    db.refresh(payment)
    return payment
