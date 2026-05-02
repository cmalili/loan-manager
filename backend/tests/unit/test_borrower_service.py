from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.models.borrower import Borrower  # noqa: E402
from app.services.borrower import (  # noqa: E402
    BorrowerNotFoundError,
    create_borrower,
    deactivate_borrower,
    get_borrower,
    update_borrower,
)
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate  # noqa: E402


class BorrowerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.borrower_id = uuid4()
        self.user_id = uuid4()
        self.borrower = Borrower(
            id=self.borrower_id,
            full_name="Jane Doe",
            phone_number="555-0101",
            external_id_number="ID-123",
            address="123 Main St",
            notes="First borrower",
            status="active",
            created_at="2026-04-11T12:00:00Z",
            updated_at="2026-04-11T12:00:00Z",
        )
        self.db = MagicMock()
        self.db.get.return_value = self.borrower
        self.db.refresh.side_effect = lambda _: None

    def test_create_borrower_records_audit_log(self) -> None:
        borrower_in = BorrowerCreate(
            full_name="Jane Doe",
            phone_number="555-0101",
            external_id_number="ID-123",
            address="123 Main St",
            notes="First borrower",
            status="active",
        )

        borrower = create_borrower(
            self.db,
            borrower_in,
            acting_user_id=self.user_id,
        )

        self.assertEqual(borrower.full_name, "Jane Doe")
        self.assertEqual(self.db.add.call_count, 2)
        self.assertEqual(self.db.add.call_args_list[1].args[0].user_id, self.user_id)
        self.assertEqual(self.db.flush.call_count, 1)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(borrower)

    def test_update_borrower_records_audit_log(self) -> None:
        borrower_in = BorrowerUpdate(phone_number="555-9999")

        borrower = update_borrower(
            self.db,
            self.borrower_id,
            borrower_in,
            acting_user_id=self.user_id,
        )

        self.assertEqual(borrower.phone_number, "555-9999")
        self.assertEqual(self.db.add.call_count, 2)
        self.assertEqual(self.db.add.call_args_list[1].args[0].user_id, self.user_id)
        self.assertEqual(self.db.flush.call_count, 1)
        self.db.commit.assert_called_once()

    def test_deactivate_borrower_records_status_change_audit_log(self) -> None:
        borrower = deactivate_borrower(
            self.db,
            self.borrower_id,
            acting_user_id=self.user_id,
        )

        self.assertEqual(borrower.status, "inactive")
        self.assertEqual(self.db.add.call_count, 2)
        self.assertEqual(self.db.add.call_args_list[1].args[0].user_id, self.user_id)
        self.assertEqual(self.db.flush.call_count, 1)
        self.db.commit.assert_called_once()

    def test_get_borrower_raises_when_missing(self) -> None:
        self.db.get.return_value = None

        with self.assertRaises(BorrowerNotFoundError):
            get_borrower(self.db, self.borrower_id)


if __name__ == "__main__":
    unittest.main()
