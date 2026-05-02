from __future__ import annotations

import os
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pydantic import ValidationError

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.models.late_charge import LateCharge  # noqa: E402
from app.models.loan import Loan  # noqa: E402
from app.models.repayment_schedule_item import RepaymentScheduleItem  # noqa: E402
from app.schemas.payment import PaymentCreate  # noqa: E402
from app.services.payment import (  # noqa: E402
    BackdatedPaymentNotAllowedError,
    PaymentValidationError,
    record_payment,
)


class PaymentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.borrower_id = uuid4()
        self.user_id = uuid4()
        self.loan_id = uuid4()
        self.loan = Loan(
            id=self.loan_id,
            borrower_id=self.borrower_id,
            created_by_user_id=self.user_id,
            principal_amount=Decimal("1000.00"),
            repayment_frequency="monthly",
            periodic_interest_rate=Decimal("30.00"),
            term_length=2,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 1),
            status="active",
            grace_period_days=7,
            notes=None,
        )
        self.borrower = MagicMock(id=self.borrower_id)
        self.user = MagicMock(id=self.user_id)
        self.db = MagicMock()
        self.db.refresh.side_effect = lambda _: None

        def fake_get(model, object_id):
            if object_id == self.loan_id:
                return self.loan
            if object_id == self.borrower_id:
                return self.borrower
            if object_id == self.user_id:
                return self.user
            return None

        self.db.get.side_effect = fake_get

    def make_payment(self, **overrides) -> PaymentCreate:
        payload = {
            "loan_id": self.loan_id,
            "borrower_id": self.borrower_id,
            "recorded_by_user_id": self.user_id,
            "amount": Decimal("100.00"),
            "payment_date": date.today(),
            "payment_method": "cash",
            "reference_code": "PMT-001",
            "notes": "Test payment",
        }
        payload.update(overrides)
        return PaymentCreate(**payload)

    def make_schedule_item(self, **overrides) -> RepaymentScheduleItem:
        item = RepaymentScheduleItem(
            id=uuid4(),
            loan_id=self.loan_id,
            installment_number=1,
            due_date=date(2026, 5, 1),
            principal_due=Decimal("500.00"),
            interest_due=Decimal("300.00"),
            principal_paid=Decimal("0.00"),
            interest_paid=Decimal("0.00"),
            waived_amount=Decimal("0.00"),
            status="pending",
        )
        for name, value in overrides.items():
            setattr(item, name, value)
        return item

    def make_late_charge(self, **overrides) -> LateCharge:
        charge = LateCharge(
            id=uuid4(),
            loan_id=self.loan_id,
            schedule_item_id=uuid4(),
            created_by_user_id=self.user_id,
            trigger_date=date(2026, 5, 9),
            base_unpaid_amount=Decimal("100.00"),
            charge_rate=Decimal("10.00"),
            charge_principal_amount=Decimal("10.00"),
            accrued_interest_amount=Decimal("2.00"),
            principal_paid=Decimal("0.00"),
            interest_paid=Decimal("0.00"),
            waived_amount=Decimal("0.00"),
            status="outstanding",
            notes=None,
        )
        for name, value in overrides.items():
            setattr(charge, name, value)
        return charge

    def test_record_payment_allocates_in_required_order(self) -> None:
        schedule_item = self.make_schedule_item()
        late_charge = self.make_late_charge()

        with patch(
            "app.services.payment.process_loan_overdue_state",
        ) as mock_process_overdue, patch(
            "app.services.payment.list_schedule_items_for_loan",
            return_value=[schedule_item],
        ), patch(
            "app.services.payment.list_late_charges_for_loan",
            return_value=[late_charge],
        ):
            payment = record_payment(self.db, self.make_payment(amount=Decimal("50.00")))

        self.assertEqual(payment.status, "recorded")
        self.assertEqual(late_charge.interest_paid, Decimal("2.00"))
        self.assertEqual(late_charge.principal_paid, Decimal("10.00"))
        self.assertEqual(schedule_item.interest_paid, Decimal("38.00"))
        self.assertEqual(schedule_item.principal_paid, Decimal("0.00"))
        self.assertEqual(schedule_item.status, "partially_paid")
        allocations = self.db.add_all.call_args.args[0]
        self.assertEqual(
            [allocation.allocation_type for allocation in allocations],
            [
                "late_charge_interest",
                "late_charge_principal",
                "regular_interest",
            ],
        )
        self.assertEqual(mock_process_overdue.call_count, 2)
        self.assertEqual(
            mock_process_overdue.call_args_list[0].kwargs["as_of_date"],
            payment.payment_date,
        )

    def test_record_payment_allocates_all_late_charge_interest_first(self) -> None:
        schedule_item = self.make_schedule_item()
        first_charge = self.make_late_charge(
            accrued_interest_amount=Decimal("2.00"),
            charge_principal_amount=Decimal("10.00"),
        )
        second_charge = self.make_late_charge(
            id=uuid4(),
            schedule_item_id=uuid4(),
            trigger_date=date(2026, 5, 10),
            accrued_interest_amount=Decimal("3.00"),
            charge_principal_amount=Decimal("10.00"),
        )

        with patch(
            "app.services.payment.process_loan_overdue_state",
        ), patch(
            "app.services.payment.list_schedule_items_for_loan",
            return_value=[schedule_item],
        ), patch(
            "app.services.payment.list_late_charges_for_loan",
            return_value=[first_charge, second_charge],
        ):
            record_payment(self.db, self.make_payment(amount=Decimal("6.00")))

        self.assertEqual(first_charge.interest_paid, Decimal("2.00"))
        self.assertEqual(second_charge.interest_paid, Decimal("3.00"))
        self.assertEqual(first_charge.principal_paid, Decimal("1.00"))
        self.assertEqual(second_charge.principal_paid, Decimal("0.00"))

        allocations = self.db.add_all.call_args.args[0]
        self.assertEqual(
            [allocation.allocation_type for allocation in allocations],
            [
                "late_charge_interest",
                "late_charge_interest",
                "late_charge_principal",
            ],
        )
        self.assertEqual(
            [allocation.late_charge_id for allocation in allocations],
            [first_charge.id, second_charge.id, first_charge.id],
        )

    def test_record_payment_allocates_all_regular_interest_first(self) -> None:
        first_item = self.make_schedule_item(
            principal_due=Decimal("50.00"),
            interest_due=Decimal("10.00"),
        )
        second_item = self.make_schedule_item(
            id=uuid4(),
            installment_number=2,
            principal_due=Decimal("50.00"),
            interest_due=Decimal("20.00"),
        )

        with patch(
            "app.services.payment.process_loan_overdue_state",
        ), patch(
            "app.services.payment.list_schedule_items_for_loan",
            return_value=[first_item, second_item],
        ), patch(
            "app.services.payment.list_late_charges_for_loan",
            return_value=[],
        ):
            record_payment(self.db, self.make_payment(amount=Decimal("35.00")))

        self.assertEqual(first_item.interest_paid, Decimal("10.00"))
        self.assertEqual(second_item.interest_paid, Decimal("20.00"))
        self.assertEqual(first_item.principal_paid, Decimal("5.00"))
        self.assertEqual(second_item.principal_paid, Decimal("0.00"))

        allocations = self.db.add_all.call_args.args[0]
        self.assertEqual(
            [allocation.allocation_type for allocation in allocations],
            ["regular_interest", "regular_interest", "regular_principal"],
        )
        self.assertEqual(
            [allocation.schedule_item_id for allocation in allocations],
            [first_item.id, second_item.id, first_item.id],
        )

    def test_record_payment_full_payoff_closes_loan(self) -> None:
        schedule_item = self.make_schedule_item(principal_due=Decimal("100.00"), interest_due=Decimal("20.00"))
        overdue_calls = {"count": 0}

        def fake_process_overdue(*args, **kwargs):
            overdue_calls["count"] += 1
            if overdue_calls["count"] == 2:
                self.loan.status = "closed"

        with patch(
            "app.services.payment.process_loan_overdue_state",
            side_effect=fake_process_overdue,
        ) as mock_process_overdue, patch(
            "app.services.payment.list_schedule_items_for_loan",
            return_value=[schedule_item],
        ), patch(
            "app.services.payment.list_late_charges_for_loan",
            return_value=[],
        ):
            payment = record_payment(self.db, self.make_payment(amount=Decimal("120.00")))

        self.assertEqual(payment.amount, Decimal("120.00"))
        self.assertEqual(schedule_item.status, "paid")
        self.assertEqual(self.loan.status, "closed")
        allocations = self.db.add_all.call_args.args[0]
        self.assertEqual(
            [allocation.allocation_type for allocation in allocations],
            ["regular_interest", "regular_principal"],
        )
        self.assertEqual(mock_process_overdue.call_count, 2)

    def test_record_payment_rejects_overpayment(self) -> None:
        schedule_item = self.make_schedule_item(principal_due=Decimal("50.00"), interest_due=Decimal("10.00"))

        with patch(
            "app.services.payment.process_loan_overdue_state",
        ), patch(
            "app.services.payment.list_schedule_items_for_loan",
            return_value=[schedule_item],
        ), patch(
            "app.services.payment.list_late_charges_for_loan",
            return_value=[],
        ):
            with self.assertRaisesRegex(PaymentValidationError, "exceeds outstanding balance"):
                record_payment(self.db, self.make_payment(amount=Decimal("70.00")))

    def test_record_payment_rejects_cancelled_loan(self) -> None:
        self.loan.status = "cancelled"

        with self.assertRaisesRegex(PaymentValidationError, "Cancelled loans"):
            record_payment(self.db, self.make_payment())

    def test_record_payment_rejects_borrower_mismatch(self) -> None:
        wrong_borrower_id = uuid4()
        wrong_borrower = MagicMock(id=wrong_borrower_id)

        def fake_get(model, object_id):
            if object_id == self.loan_id:
                return self.loan
            if object_id == self.borrower_id:
                return self.borrower
            if object_id == wrong_borrower_id:
                return wrong_borrower
            if object_id == self.user_id:
                return self.user
            return None

        self.db.get.side_effect = fake_get

        with self.assertRaisesRegex(PaymentValidationError, "must match the loan borrower"):
            record_payment(
                self.db,
                self.make_payment(borrower_id=wrong_borrower_id),
            )

    def test_record_payment_rejects_backdated_payment_for_non_admin_user(self) -> None:
        self.user.role = "staff"

        with self.assertRaisesRegex(
            BackdatedPaymentNotAllowedError,
            "Only admin users may record backdated payments",
        ):
            record_payment(
                self.db,
                self.make_payment(payment_date=date.today() - timedelta(days=1)),
            )

    def test_payment_schema_rejects_more_than_two_decimal_places(self) -> None:
        with self.assertRaises(ValidationError):
            self.make_payment(amount=Decimal("10.001"))


if __name__ == "__main__":
    unittest.main()
