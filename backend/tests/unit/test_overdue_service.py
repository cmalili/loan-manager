from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.models.late_charge import LateCharge  # noqa: E402
from app.models.loan import Loan  # noqa: E402
from app.models.repayment_schedule_item import RepaymentScheduleItem  # noqa: E402
from app.services.overdue import (  # noqa: E402
    process_loan_overdue_state,
)


class OverdueServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loan_id = uuid4()
        self.borrower_id = uuid4()
        self.user_id = uuid4()
        self.db = MagicMock()

    def make_loan(self, **overrides) -> Loan:
        loan = Loan(
            id=self.loan_id,
            borrower_id=self.borrower_id,
            created_by_user_id=self.user_id,
            principal_amount=Decimal("1000.00"),
            repayment_frequency="weekly",
            periodic_interest_rate=Decimal("8.00"),
            term_length=4,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 29),
            status="active",
            grace_period_days=7,
            notes=None,
        )
        for name, value in overrides.items():
            setattr(loan, name, value)
        return loan

    def make_schedule_item(self, **overrides) -> RepaymentScheduleItem:
        item = RepaymentScheduleItem(
            id=uuid4(),
            loan_id=self.loan_id,
            installment_number=1,
            due_date=date(2026, 4, 1),
            principal_due=Decimal("100.00"),
            interest_due=Decimal("20.00"),
            principal_paid=Decimal("0.00"),
            interest_paid=Decimal("0.00"),
            waived_amount=Decimal("0.00"),
            status="pending",
        )
        item.late_charge = None
        for name, value in overrides.items():
            setattr(item, name, value)
        return item

    def make_late_charge(self, **overrides) -> LateCharge:
        charge = LateCharge(
            id=uuid4(),
            loan_id=self.loan_id,
            schedule_item_id=uuid4(),
            created_by_user_id=self.user_id,
            trigger_date=date(2026, 4, 8),
            base_unpaid_amount=Decimal("120.00"),
            charge_rate=Decimal("10.00"),
            charge_principal_amount=Decimal("12.00"),
            accrued_interest_amount=Decimal("0.00"),
            principal_paid=Decimal("0.00"),
            interest_paid=Decimal("0.00"),
            waived_amount=Decimal("0.00"),
            interest_periods_accrued=0,
            status="outstanding",
            notes=None,
        )
        for name, value in overrides.items():
            setattr(charge, name, value)
        return charge

    def test_process_loan_marks_schedule_item_overdue_and_creates_one_late_charge(self) -> None:
        loan = self.make_loan()
        item = self.make_schedule_item()

        with patch(
            "app.services.overdue.list_schedule_items_for_loan",
            return_value=[item],
        ), patch(
            "app.services.overdue.list_late_charges_for_loan",
            side_effect=lambda db, loan_id: [item.late_charge] if item.late_charge else [],
        ):
            result = process_loan_overdue_state(
                self.db,
                loan,
                as_of_date=date(2026, 4, 9),
                created_by_user_id=self.user_id,
            )

        self.assertEqual(item.status, "overdue")
        self.assertIsNotNone(item.late_charge)
        self.assertEqual(item.late_charge.schedule_item_id, item.id)
        self.assertEqual(item.late_charge.base_unpaid_amount, Decimal("120.00"))
        self.assertEqual(item.late_charge.charge_principal_amount, Decimal("12.00"))
        self.assertEqual(item.late_charge.charge_rate, Decimal("10.00"))
        self.assertEqual(result.schedule_items_marked_overdue, 1)
        self.assertEqual(result.late_charges_created, 1)
        self.assertEqual(loan.status, "overdue")
        self.assertEqual(self.db.add.call_count, 3)
        self.db.flush.assert_called_once()

    def test_process_loan_accrues_late_charge_interest_by_completed_periods(self) -> None:
        loan = self.make_loan()
        item = self.make_schedule_item(status="overdue")
        charge = self.make_late_charge(schedule_item_id=item.id)
        item.late_charge = charge

        with patch(
            "app.services.overdue.list_schedule_items_for_loan",
            return_value=[item],
        ), patch(
            "app.services.overdue.list_late_charges_for_loan",
            return_value=[charge],
        ):
            result = process_loan_overdue_state(
                self.db,
                loan,
                as_of_date=date(2026, 4, 22),
                created_by_user_id=self.user_id,
            )

        self.assertEqual(charge.accrued_interest_amount, Decimal("1.92"))
        self.assertEqual(charge.interest_periods_accrued, 2)
        self.assertEqual(result.late_charges_accrued, 1)
        self.assertEqual(charge.status, "outstanding")

    def test_process_loan_cures_overdue_status_when_overdue_items_are_fully_settled(self) -> None:
        loan = self.make_loan(status="overdue")
        paid_item = self.make_schedule_item(
            principal_paid=Decimal("100.00"),
            interest_paid=Decimal("20.00"),
            status="overdue",
        )
        future_item = self.make_schedule_item(
            installment_number=2,
            due_date=date(2026, 5, 1),
            status="pending",
        )

        with patch(
            "app.services.overdue.list_schedule_items_for_loan",
            return_value=[paid_item, future_item],
        ), patch(
            "app.services.overdue.list_late_charges_for_loan",
            return_value=[],
        ):
            process_loan_overdue_state(
                self.db,
                loan,
                as_of_date=date(2026, 4, 10),
                created_by_user_id=self.user_id,
            )

        self.assertEqual(paid_item.status, "paid")
        self.assertEqual(future_item.status, "pending")
        self.assertEqual(loan.status, "active")


if __name__ == "__main__":
    unittest.main()
