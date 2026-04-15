from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException, status

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.routes.loans import create_loan_endpoint  # noqa: E402
from app.schemas.loan import LoanCreate  # noqa: E402
from app.services.loan import (  # noqa: E402
    ActiveLoanConflictError,
    LoanBorrowerNotFoundError,
    LoanCreatorNotFoundError,
    LoanValidationError,
)


class LoanRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_db = object()
        self.borrower_id = uuid4()
        self.user_id = uuid4()
        self.current_user = type("UserStub", (), {"id": self.user_id, "role": "admin"})()
        self.loan_payload = {
            "id": uuid4(),
            "borrower_id": self.borrower_id,
            "created_by_user_id": self.user_id,
            "principal_amount": Decimal("1000.00"),
            "repayment_frequency": "monthly",
            "periodic_interest_rate": Decimal("30.00"),
            "term_length": 3,
            "start_date": date(2026, 4, 11),
            "end_date": date(2026, 7, 11),
            "status": "draft",
            "grace_period_days": 7,
            "notes": "Test loan",
            "created_at": "2026-04-11T12:00:00Z",
            "updated_at": "2026-04-11T12:00:00Z",
        }

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

    def test_create_loan_returns_created_loan(self) -> None:
        payload = self.make_payload(status="active")

        with patch(
            "app.api.routes.loans.create_loan",
            return_value=self.loan_payload,
        ) as mock_create_loan:
            result = create_loan_endpoint(payload, self.fake_db, self.current_user)

        self.assertEqual(result["borrower_id"], self.borrower_id)
        mock_create_loan.assert_called_once_with(self.fake_db, payload)

    def test_create_loan_returns_404_when_borrower_is_missing(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.loans.create_loan",
            side_effect=LoanBorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_loan_endpoint(payload, self.fake_db, self.current_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")

    def test_create_loan_returns_404_when_creator_is_missing(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.loans.create_loan",
            side_effect=LoanCreatorNotFoundError("User not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_loan_endpoint(payload, self.fake_db, self.current_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "User not found")

    def test_create_loan_returns_409_on_active_loan_conflict(self) -> None:
        payload = self.make_payload(status="active")

        with patch(
            "app.api.routes.loans.create_loan",
            side_effect=ActiveLoanConflictError("Borrower already has an active loan"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_loan_endpoint(payload, self.fake_db, self.current_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(exc_info.exception.detail, "Borrower already has an active loan")

    def test_create_loan_returns_400_on_rule_violation(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.loans.create_loan",
            side_effect=LoanValidationError("Grace period must be 7 days in Version 1"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                create_loan_endpoint(payload, self.fake_db, self.current_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            exc_info.exception.detail,
            "Grace period must be 7 days in Version 1",
        )

    def test_create_loan_returns_403_when_authenticated_user_mismatches_creator(self) -> None:
        payload = self.make_payload()
        other_user = type("UserStub", (), {"id": uuid4(), "role": "admin"})()

        with self.assertRaises(HTTPException) as exc_info:
            create_loan_endpoint(payload, self.fake_db, other_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            exc_info.exception.detail,
            "Authenticated user must match created_by_user_id",
        )


if __name__ == "__main__":
    unittest.main()
