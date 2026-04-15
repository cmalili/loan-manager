"""Payment service layer."""

from __future__ import annotations

from datetime import datetime
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


ZERO = Decimal("0.00")


class PaymentValidationError(ValueError):
    """Raised when a payment violates business rules."""


class PaymentLoanNotFoundError(LookupError):
    """Raised when a payment references a missing loan."""


class PaymentBorrowerNotFoundError(LookupError):
    """Raised when a payment references a missing borrower."""


class PaymentRecorderNotFoundError(LookupError):
    """Raised when a payment references a missing user."""


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


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
    return _money(charge.charge_principal_amount - charge.principal_paid - charge.waived_amount)


def total_outstanding_balance(schedule_items: list[RepaymentScheduleItem], late_charges: list[LateCharge]) -> Decimal:
    total = ZERO
    for charge in late_charges:
        total += late_charge_interest_outstanding(charge)
        total += late_charge_principal_outstanding(charge)
    for item in schedule_items:
        total += schedule_item_regular_interest_outstanding(item)
        total += schedule_item_regular_principal_outstanding(item)
    return _money(total)


def apply_payment_to_late_charges(
    payment: Payment,
    late_charges: list[LateCharge],
    amount_remaining: Decimal,
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    for charge in late_charges:
        if amount_remaining <= ZERO:
            break

        interest_outstanding = late_charge_interest_outstanding(charge)
        if interest_outstanding > ZERO and amount_remaining > ZERO:
            amount_to_apply = min(amount_remaining, interest_outstanding)
            charge.interest_paid = _money(charge.interest_paid + amount_to_apply)
            allocations.append(
                PaymentAllocation(
                    payment_id=payment.id,
                    loan_id=payment.loan_id,
                    late_charge_id=charge.id,
                    allocation_type="late_charge_interest",
                    amount=amount_to_apply,
                )
            )
            amount_remaining = _money(amount_remaining - amount_to_apply)

        principal_outstanding = late_charge_principal_outstanding(charge)
        if principal_outstanding > ZERO and amount_remaining > ZERO:
            amount_to_apply = min(amount_remaining, principal_outstanding)
            charge.principal_paid = _money(charge.principal_paid + amount_to_apply)
            allocations.append(
                PaymentAllocation(
                    payment_id=payment.id,
                    loan_id=payment.loan_id,
                    late_charge_id=charge.id,
                    allocation_type="late_charge_principal",
                    amount=amount_to_apply,
                )
            )
            amount_remaining = _money(amount_remaining - amount_to_apply)

        if late_charge_interest_outstanding(charge) == ZERO and late_charge_principal_outstanding(charge) == ZERO:
            charge.status = "paid"
        elif charge.interest_paid > ZERO or charge.principal_paid > ZERO:
            charge.status = "partially_paid"

    return allocations, amount_remaining


def apply_payment_to_schedule_items(
    payment: Payment,
    schedule_items: list[RepaymentScheduleItem],
    amount_remaining: Decimal,
) -> tuple[list[PaymentAllocation], Decimal]:
    allocations: list[PaymentAllocation] = []

    for item in schedule_items:
        if amount_remaining <= ZERO:
            break

        interest_outstanding = schedule_item_regular_interest_outstanding(item)
        if interest_outstanding > ZERO and amount_remaining > ZERO:
            amount_to_apply = min(amount_remaining, interest_outstanding)
            item.interest_paid = _money(item.interest_paid + amount_to_apply)
            allocations.append(
                PaymentAllocation(
                    payment_id=payment.id,
                    loan_id=payment.loan_id,
                    schedule_item_id=item.id,
                    allocation_type="regular_interest",
                    amount=amount_to_apply,
                )
            )
            amount_remaining = _money(amount_remaining - amount_to_apply)

        principal_outstanding = schedule_item_regular_principal_outstanding(item)
        if principal_outstanding > ZERO and amount_remaining > ZERO:
            amount_to_apply = min(amount_remaining, principal_outstanding)
            item.principal_paid = _money(item.principal_paid + amount_to_apply)
            allocations.append(
                PaymentAllocation(
                    payment_id=payment.id,
                    loan_id=payment.loan_id,
                    schedule_item_id=item.id,
                    allocation_type="regular_principal",
                    amount=amount_to_apply,
                )
            )
            amount_remaining = _money(amount_remaining - amount_to_apply)

        if schedule_item_regular_interest_outstanding(item) == ZERO and schedule_item_regular_principal_outstanding(item) == ZERO:
            item.status = "paid"
        elif item.interest_paid > ZERO or item.principal_paid > ZERO:
            item.status = "partially_paid"

    return allocations, amount_remaining


def record_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    """Record a payment and allocate it across the loan obligations."""

    loan = db.get(Loan, payment_in.loan_id)
    if loan is None:
        raise PaymentLoanNotFoundError(f"Loan {payment_in.loan_id} was not found")

    borrower = db.get(Borrower, payment_in.borrower_id)
    if borrower is None:
        raise PaymentBorrowerNotFoundError(f"Borrower {payment_in.borrower_id} was not found")

    recorder = db.get(User, payment_in.recorded_by_user_id)
    if recorder is None:
        raise PaymentRecorderNotFoundError(f"User {payment_in.recorded_by_user_id} was not found")

    if loan.borrower_id != payment_in.borrower_id:
        raise PaymentValidationError("Payment borrower must match the loan borrower")

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
        is_backdated=payment_in.payment_date < datetime.now().date(),
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

    updated_outstanding = total_outstanding_balance(schedule_items, late_charges)
    if updated_outstanding == ZERO:
        loan.status = "closed"

    db.commit()
    db.refresh(payment)
    return payment
