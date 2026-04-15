from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException, status

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.routes.borrowers import (  # noqa: E402
    BorrowerNotFoundError,
    create_borrower_endpoint,
    deactivate_borrower_endpoint,
    get_borrower_endpoint,
    list_borrower_loans_endpoint,
    update_borrower_endpoint,
)
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate  # noqa: E402


class BorrowerRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_db = object()
        self.current_user = SimpleNamespace(id=uuid4(), role="admin")
        self.borrower_id = uuid4()
        self.borrower_payload = {
            "id": self.borrower_id,
            "full_name": "Jane Doe",
            "phone_number": "555-0101",
            "external_id_number": "ID-123",
            "address": "123 Main St",
            "notes": "First borrower",
            "status": "active",
            "created_at": "2026-04-11T12:00:00Z",
            "updated_at": "2026-04-11T12:00:00Z",
        }

    def test_get_borrower_returns_borrower(self) -> None:
        with patch(
            "app.api.routes.borrowers.get_borrower",
            return_value=self.borrower_payload,
        ) as mock_get_borrower:
            result = get_borrower_endpoint(self.borrower_id, self.fake_db, self.current_user)

        self.assertEqual(result["id"], self.borrower_id)
        mock_get_borrower.assert_called_once_with(self.fake_db, self.borrower_id)

    def test_get_borrower_returns_404_when_missing(self) -> None:
        with patch(
            "app.api.routes.borrowers.get_borrower",
            side_effect=BorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                get_borrower_endpoint(self.borrower_id, self.fake_db, self.current_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")

    def test_create_borrower_passes_schema_to_service(self) -> None:
        borrower_in = BorrowerCreate(
            full_name="Jane Doe",
            phone_number="555-0101",
            external_id_number="ID-123",
            address="123 Main St",
            notes="First borrower",
            status="active",
        )

        with patch(
            "app.api.routes.borrowers.create_borrower",
            return_value=self.borrower_payload,
        ) as mock_create_borrower:
            result = create_borrower_endpoint(borrower_in, self.fake_db, self.current_user)

        self.assertEqual(result["full_name"], "Jane Doe")
        mock_create_borrower.assert_called_once_with(self.fake_db, borrower_in)

    def test_list_borrower_loans_returns_history(self) -> None:
        loan_payload = [
            {
                "id": uuid4(),
                "borrower_id": self.borrower_id,
                "created_by_user_id": uuid4(),
                "principal_amount": "1000.00",
                "repayment_frequency": "weekly",
                "periodic_interest_rate": "8.00",
                "term_length": 4,
                "start_date": "2026-04-01",
                "end_date": "2026-04-29",
                "status": "closed",
                "grace_period_days": 7,
                "notes": None,
                "created_at": "2026-04-11T12:00:00Z",
                "updated_at": "2026-04-11T12:00:00Z",
            }
        ]

        with patch(
            "app.api.routes.borrowers.list_borrower_loan_history",
            return_value=loan_payload,
        ) as mock_history:
            result = list_borrower_loans_endpoint(
                self.borrower_id, self.fake_db, self.current_user
            )

        self.assertEqual(result, loan_payload)
        mock_history.assert_called_once_with(self.fake_db, self.borrower_id)

    def test_list_borrower_loans_returns_404_when_borrower_missing(self) -> None:
        with patch(
            "app.api.routes.borrowers.list_borrower_loan_history",
            side_effect=BorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                list_borrower_loans_endpoint(
                    self.borrower_id, self.fake_db, self.current_user
                )

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")

    def test_update_borrower_passes_partial_schema_to_service(self) -> None:
        borrower_in = BorrowerUpdate(
            phone_number="555-9999",
            notes="Updated contact details",
        )
        updated_payload = dict(self.borrower_payload)
        updated_payload["phone_number"] = "555-9999"
        updated_payload["notes"] = "Updated contact details"

        with patch(
            "app.api.routes.borrowers.update_borrower",
            return_value=updated_payload,
        ) as mock_update_borrower:
            result = update_borrower_endpoint(
                self.borrower_id, borrower_in, self.fake_db, self.current_user
            )

        self.assertEqual(result["phone_number"], "555-9999")
        mock_update_borrower.assert_called_once_with(
            self.fake_db, self.borrower_id, borrower_in
        )

    def test_update_borrower_returns_404_when_missing(self) -> None:
        borrower_in = BorrowerUpdate(notes="Does not exist")

        with patch(
            "app.api.routes.borrowers.update_borrower",
            side_effect=BorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                update_borrower_endpoint(
                    self.borrower_id, borrower_in, self.fake_db, self.current_user
                )

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")

    def test_deactivate_borrower_returns_inactive_borrower(self) -> None:
        inactive_payload = dict(self.borrower_payload)
        inactive_payload["status"] = "inactive"

        with patch(
            "app.api.routes.borrowers.deactivate_borrower",
            return_value=inactive_payload,
        ) as mock_deactivate_borrower:
            result = deactivate_borrower_endpoint(
                self.borrower_id, self.fake_db, self.current_user
            )

        self.assertEqual(result["status"], "inactive")
        mock_deactivate_borrower.assert_called_once_with(self.fake_db, self.borrower_id)

    def test_deactivate_borrower_returns_404_when_missing(self) -> None:
        with patch(
            "app.api.routes.borrowers.deactivate_borrower",
            side_effect=BorrowerNotFoundError("Borrower not found"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                deactivate_borrower_endpoint(
                    self.borrower_id, self.fake_db, self.current_user
                )

        self.assertEqual(exc_info.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc_info.exception.detail, "Borrower not found")


if __name__ == "__main__":
    unittest.main()
