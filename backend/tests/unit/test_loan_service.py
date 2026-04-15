from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.services.loan import (  # noqa: E402
    ActiveLoanConflictError,
    LoanBorrowerNotFoundError,
    LoanCreatorNotFoundError,
    LoanValidationError,
    calculate_end_date,
    create_loan,
    get_periodic_interest_rate,
)
from app.schemas.loan import LoanCreate  # noqa: E402


class LoanServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.borrower_id = uuid4()
        self.user_id = uuid4()
        self.borrower = MagicMock(id=self.borrower_id)
        self.user = MagicMock(id=self.user_id)
        self.db = MagicMock()

        def fake_get(model, object_id):
            if object_id == self.borrower_id:
                return self.borrower
            if object_id == self.user_id:
                return self.user
            return None

        self.db.get.side_effect = fake_get
        self.db.scalar.return_value = None
        self.db.refresh.side_effect = lambda _: None

    def make_payload(self, **overrides) -> LoanCreate:
        payload = {
            "borrower_id": self.borrower_id,
            "created_by_user_id": self.user_id,
            "principal_amount": Decimal("1000.00"),
            "repayment_frequency": "monthly",
            "term_length": 3,
            "start_date": date(2026, 4, 11),
            "status": "draft",
            "grace_period_days": 7,
            "notes": "Test loan",
        }
        payload.update(overrides)
        return LoanCreate(**payload)

    def test_calculate_end_date_supports_weekly_and_monthly(self) -> None:
        self.assertEqual(
            calculate_end_date(date(2026, 4, 11), "weekly", 4),
            date(2026, 5, 9),
        )
        self.assertEqual(
            calculate_end_date(date(2026, 4, 11), "monthly", 3),
            date(2026, 7, 11),
        )

    def test_get_periodic_interest_rate_uses_standard_v1_rates(self) -> None:
        self.assertEqual(get_periodic_interest_rate("weekly"), Decimal("8.00"))
        self.assertEqual(get_periodic_interest_rate("monthly"), Decimal("30.00"))

    def test_create_loan_computes_end_date_and_standard_rate(self) -> None:
        loan = create_loan(self.db, self.make_payload(status="active"))

        self.assertEqual(loan.borrower_id, self.borrower_id)
        self.assertEqual(loan.created_by_user_id, self.user_id)
        self.assertEqual(loan.periodic_interest_rate, Decimal("30.00"))
        self.assertEqual(loan.end_date, date(2026, 7, 11))
        self.assertEqual(loan.status, "active")
        self.assertEqual(self.db.add.call_count, 2)
        self.assertIs(self.db.add.call_args_list[0].args[0], loan)
        self.db.flush.assert_called_once()
        self.db.add_all.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(loan)

    def test_create_loan_raises_when_borrower_is_missing(self) -> None:
        missing_borrower_id = uuid4()
        payload = self.make_payload(borrower_id=missing_borrower_id)

        with self.assertRaises(LoanBorrowerNotFoundError):
            create_loan(self.db, payload)

    def test_create_loan_raises_when_creator_is_missing(self) -> None:
        missing_user_id = uuid4()
        payload = self.make_payload(created_by_user_id=missing_user_id)

        with self.assertRaises(LoanCreatorNotFoundError):
            create_loan(self.db, payload)

    def test_create_loan_rejects_non_standard_grace_period(self) -> None:
        with self.assertRaisesRegex(LoanValidationError, "Grace period must be 7 days"):
            create_loan(self.db, self.make_payload(grace_period_days=10))

    def test_create_loan_rejects_second_active_loan_for_borrower(self) -> None:
        self.db.scalar.return_value = MagicMock()

        with self.assertRaises(ActiveLoanConflictError):
            create_loan(self.db, self.make_payload(status="active"))

    def test_create_loan_allows_draft_even_if_active_loan_exists(self) -> None:
        self.db.scalar.return_value = MagicMock()

        loan = create_loan(self.db, self.make_payload(status="draft"))

        self.assertEqual(loan.status, "draft")


if __name__ == "__main__":
    unittest.main()
