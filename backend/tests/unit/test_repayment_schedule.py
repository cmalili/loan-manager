from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.models.loan import Loan  # noqa: E402
from app.services.repayment_schedule import (  # noqa: E402
    build_repayment_schedule,
    build_schedule_items,
)


class RepaymentScheduleTests(unittest.TestCase):
    def make_loan(
        self,
        *,
        principal_amount: Decimal,
        repayment_frequency: str,
        periodic_interest_rate: Decimal,
        term_length: int,
        start_date: date,
    ) -> Loan:
        return Loan(
            id=uuid4(),
            borrower_id=uuid4(),
            created_by_user_id=uuid4(),
            principal_amount=principal_amount,
            repayment_frequency=repayment_frequency,
            periodic_interest_rate=periodic_interest_rate,
            term_length=term_length,
            start_date=start_date,
            end_date=start_date,
            status="draft",
            grace_period_days=7,
            notes=None,
        )

    def test_weekly_schedule_has_expected_due_dates_and_totals(self) -> None:
        loan = self.make_loan(
            principal_amount=Decimal("1000.00"),
            repayment_frequency="weekly",
            periodic_interest_rate=Decimal("8.00"),
            term_length=4,
            start_date=date(2026, 4, 11),
        )

        schedule = build_repayment_schedule(loan)

        self.assertEqual(len(schedule), 4)
        self.assertEqual(schedule[0].due_date, date(2026, 4, 18))
        self.assertEqual(schedule[1].due_date, date(2026, 4, 25))
        self.assertEqual(schedule[2].due_date, date(2026, 5, 2))
        self.assertEqual(schedule[3].due_date, date(2026, 5, 9))
        self.assertEqual(sum(item.principal_due for item in schedule), Decimal("1000.00"))
        self.assertEqual(sum(item.interest_due for item in schedule), Decimal("200.00"))
        self.assertEqual(schedule[0].interest_due, Decimal("80.00"))
        self.assertEqual(schedule[-1].interest_due, Decimal("20.00"))

    def test_monthly_schedule_handles_rounding_in_final_installment(self) -> None:
        loan = self.make_loan(
            principal_amount=Decimal("1000.00"),
            repayment_frequency="monthly",
            periodic_interest_rate=Decimal("30.00"),
            term_length=3,
            start_date=date(2026, 1, 31),
        )

        schedule = build_repayment_schedule(loan)

        self.assertEqual(len(schedule), 3)
        self.assertEqual(schedule[0].due_date, date(2026, 2, 28))
        self.assertEqual(schedule[1].due_date, date(2026, 3, 31))
        self.assertEqual(schedule[2].due_date, date(2026, 4, 30))
        self.assertEqual(schedule[0].principal_due, Decimal("333.33"))
        self.assertEqual(schedule[1].principal_due, Decimal("333.33"))
        self.assertEqual(schedule[2].principal_due, Decimal("333.34"))
        self.assertEqual(sum(item.principal_due for item in schedule), Decimal("1000.00"))
        self.assertEqual(sum(item.interest_due for item in schedule), Decimal("600.00"))

    def test_build_schedule_items_returns_pending_orm_rows(self) -> None:
        loan = self.make_loan(
            principal_amount=Decimal("500.00"),
            repayment_frequency="weekly",
            periodic_interest_rate=Decimal("8.00"),
            term_length=2,
            start_date=date(2026, 4, 11),
        )

        items = build_schedule_items(loan)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].loan_id, loan.id)
        self.assertEqual(items[0].installment_number, 1)
        self.assertEqual(items[0].status, "pending")
        self.assertEqual(items[1].installment_number, 2)


if __name__ == "__main__":
    unittest.main()
