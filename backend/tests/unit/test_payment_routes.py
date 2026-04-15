from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException, status

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.routes.payments import record_payment_endpoint  # noqa: E402
from app.schemas.payment import PaymentCreate  # noqa: E402
from app.services.payment import (  # noqa: E402
    PaymentBorrowerNotFoundError,
    PaymentLoanNotFoundError,
    PaymentRecorderNotFoundError,
    PaymentValidationError,
)


class PaymentRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_db = object()
        self.payment_payload = {
            "id": uuid4(),
            "loan_id": uuid4(),
            "borrower_id": uuid4(),
            "recorded_by_user_id": uuid4(),
            "amount": Decimal("100.00"),
            "payment_date": date(2026, 4, 11),
            "recorded_at": "2026-04-11T12:00:00Z",
            "payment_method": "cash",
            "reference_code": "PMT-001",
            "notes": "Test payment",
            "is_backdated": False,
            "status": "recorded",
            "created_at": "2026-04-11T12:00:00Z",
            "updated_at": "2026-04-11T12:00:00Z",
            "allocations": [],
        }

    def make_payload(self) -> PaymentCreate:
        return PaymentCreate(
            loan_id=self.payment_payload["loan_id"],
            borrower_id=self.payment_payload["borrower_id"],
            recorded_by_user_id=self.payment_payload["recorded_by_user_id"],
            amount=Decimal("100.00"),
            payment_date=date(2026, 4, 11),
            payment_method="cash",
            reference_code="PMT-001",
            notes="Test payment",
        )

    def test_record_payment_returns_created_payment(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.payments.record_payment",
            return_value=self.payment_payload,
        ) as mock_record_payment:
            result = record_payment_endpoint(payload, self.fake_db)

        self.assertEqual(result["status"], "recorded")
        mock_record_payment.assert_called_once_with(self.fake_db, payload)

    def test_record_payment_returns_404_when_loan_missing(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.payments.record_payment",
            side_effect=PaymentLoanNotFoundError("Loan not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                record_payment_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Loan not found")

    def test_record_payment_returns_404_when_borrower_missing(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.payments.record_payment",
            side_effect=PaymentBorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                record_payment_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")

    def test_record_payment_returns_404_when_user_missing(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.payments.record_payment",
            side_effect=PaymentRecorderNotFoundError("User not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                record_payment_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "User not found")

    def test_record_payment_returns_400_on_validation_error(self) -> None:
        payload = self.make_payload()

        with patch(
            "app.api.routes.payments.record_payment",
            side_effect=PaymentValidationError("Payment amount exceeds outstanding balance"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                record_payment_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            exc_info.exception.detail,
            "Payment amount exceeds outstanding balance",
        )


if __name__ == "__main__":
    unittest.main()
