from __future__ import annotations

import os
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.models.borrower import Borrower  # noqa: E402
from app.models.late_charge import LateCharge  # noqa: E402
from app.models.loan import Loan  # noqa: E402
from app.models.payment import Payment  # noqa: E402
from app.models.repayment_schedule_item import RepaymentScheduleItem  # noqa: E402
from app.services.reporting import (  # noqa: E402
    build_overdue_loan_summary,
    get_dashboard_summary,
    list_borrower_loan_history,
    list_overdue_loans,
    list_recent_payments,
)


class ReportingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.borrower_id = uuid4()
        self.loan_id = uuid4()
        self.user_id = uuid4()
        self.db = MagicMock()

    def make_loan(self, **overrides) -> Loan:
        loan = Loan(
            id=self.loan_id,
            borrower_id=self.borrower_id,
            created_by_user_id=uuid4(),
            principal_amount=Decimal("1000.00"),
            repayment_frequency="weekly",
            periodic_interest_rate=Decimal("8.00"),
            term_length=4,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 29),
            status="overdue",
            grace_period_days=7,
            notes=None,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        loan.borrower = Borrower(
            id=self.borrower_id,
            full_name="Jane Doe",
            phone_number="555-0101",
            external_id_number="ID-123",
            address="123 Main St",
            notes=None,
            status="active",
        )
        loan.schedule_items = []
        loan.late_charges = []
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
            status="overdue",
        )
        for name, value in overrides.items():
            setattr(item, name, value)
        return item

    def make_late_charge(self, **overrides) -> LateCharge:
        charge = LateCharge(
            id=uuid4(),
            loan_id=self.loan_id,
            schedule_item_id=uuid4(),
            created_by_user_id=uuid4(),
            trigger_date=date(2026, 4, 8),
            base_unpaid_amount=Decimal("120.00"),
            charge_rate=Decimal("10.00"),
            charge_principal_amount=Decimal("12.00"),
            accrued_interest_amount=Decimal("1.00"),
            principal_paid=Decimal("2.00"),
            interest_paid=Decimal("0.25"),
            waived_amount=Decimal("0.00"),
            interest_periods_accrued=1,
            status="partially_paid",
            notes=None,
        )
        for name, value in overrides.items():
            setattr(charge, name, value)
        return charge

    def make_payment(self, **overrides) -> Payment:
        payment = Payment(
            id=uuid4(),
            loan_id=self.loan_id,
            borrower_id=self.borrower_id,
            recorded_by_user_id=uuid4(),
            amount=Decimal("50.00"),
            payment_date=date(2026, 4, 12),
            recorded_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
            payment_method="cash",
            reference_code="PMT-001",
            notes=None,
            is_backdated=False,
            status="recorded",
            created_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
        )
        payment.allocations = []
        for name, value in overrides.items():
            setattr(payment, name, value)
        return payment

    def test_list_borrower_loan_history_requires_existing_borrower(self) -> None:
        loans = [self.make_loan()]
        scalars_result = MagicMock()
        scalars_result.all.return_value = loans
        self.db.scalars.return_value = scalars_result

        with patch("app.services.reporting.get_borrower") as mock_get_borrower:
            result = list_borrower_loan_history(self.db, self.borrower_id)

        self.assertEqual(result, loans)
        mock_get_borrower.assert_called_once_with(self.db, self.borrower_id)

    def test_build_overdue_loan_summary_uses_source_of_truth_balances(self) -> None:
        loan = self.make_loan()
        loan.schedule_items = [self.make_schedule_item()]
        loan.late_charges = [self.make_late_charge()]

        summary = build_overdue_loan_summary(loan, as_of_date=date(2026, 4, 15))

        self.assertEqual(summary.borrower_name, "Jane Doe")
        self.assertEqual(summary.days_overdue, 14)
        self.assertEqual(summary.overdue_installment_count, 1)
        self.assertEqual(summary.overdue_regular_balance, Decimal("120.00"))
        self.assertEqual(summary.outstanding_late_charge_balance, Decimal("10.75"))
        self.assertEqual(summary.total_overdue_balance, Decimal("130.75"))

    def test_list_overdue_loans_processes_overdue_state_before_querying(self) -> None:
        loan = self.make_loan()
        loan.schedule_items = [self.make_schedule_item()]
        loan.late_charges = [self.make_late_charge()]
        scalars_result = MagicMock()
        scalars_result.all.return_value = [loan]
        self.db.scalars.return_value = scalars_result

        with patch("app.services.reporting.process_overdue_loans") as mock_process:
            result = list_overdue_loans(
                self.db,
                as_of_date=date(2026, 4, 15),
                acting_user_id=self.user_id,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].loan_id, loan.id)
        mock_process.assert_called_once_with(
            self.db,
            as_of_date=date(2026, 4, 15),
            created_by_user_id=self.user_id,
        )

    def test_list_recent_payments_returns_recorded_payments(self) -> None:
        payments = [self.make_payment()]
        scalars_result = MagicMock()
        scalars_result.all.return_value = payments
        self.db.scalars.return_value = scalars_result

        result = list_recent_payments(self.db, limit=5)

        self.assertEqual(result, payments)

    def test_get_dashboard_summary_combines_counts_and_balances(self) -> None:
        active_loan = self.make_loan(status="active")
        active_loan.schedule_items = [
            self.make_schedule_item(status="pending", due_date=date(2026, 4, 20))
        ]
        active_loan.late_charges = []

        closed_loan = self.make_loan(status="closed", id=uuid4())
        closed_loan.schedule_items = [
            self.make_schedule_item(
                loan_id=closed_loan.id,
                principal_paid=Decimal("100.00"),
                interest_paid=Decimal("20.00"),
                status="paid",
            )
        ]
        closed_loan.late_charges = []

        scalars_loans = MagicMock()
        scalars_loans.all.return_value = [active_loan, closed_loan]
        scalars_recent = MagicMock()
        scalars_recent.all.return_value = [
            self.make_payment(amount=Decimal("50.00")),
            self.make_payment(amount=Decimal("75.00"), id=uuid4()),
        ]
        self.db.scalars.side_effect = [scalars_loans, scalars_recent]

        overdue_rows = [SimpleNamespace(total_overdue_balance=Decimal("130.75"))]
        with patch(
            "app.services.reporting.list_overdue_loans",
            return_value=overdue_rows,
        ) as mock_overdue:
            summary = get_dashboard_summary(
                self.db,
                as_of_date=date(2026, 4, 15),
                acting_user_id=self.user_id,
            )

        self.assertEqual(summary["active_loan_count"], 1)
        self.assertEqual(summary["closed_loan_count"], 1)
        self.assertEqual(summary["overdue_loan_count"], 1)
        self.assertEqual(summary["total_outstanding_balance"], Decimal("120.00"))
        self.assertEqual(summary["total_overdue_balance"], Decimal("130.75"))
        self.assertEqual(summary["recent_payment_count"], 2)
        self.assertEqual(summary["recent_payment_total"], Decimal("125.00"))
        mock_overdue.assert_called_once_with(
            self.db,
            as_of_date=date(2026, 4, 15),
            acting_user_id=self.user_id,
        )


if __name__ == "__main__":
    unittest.main()
