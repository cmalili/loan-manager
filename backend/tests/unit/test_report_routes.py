from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.routes.reports import (  # noqa: E402
    get_dashboard_summary_endpoint,
    list_overdue_loans_endpoint,
    list_recent_payments_endpoint,
)


class ReportRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_db = object()
        self.current_user = type("UserStub", (), {"id": uuid4(), "role": "admin"})()

    def test_list_overdue_loans_returns_report_rows(self) -> None:
        rows = [
            {
                "loan_id": uuid4(),
                "borrower_id": uuid4(),
                "borrower_name": "Jane Doe",
                "loan_status": "overdue",
                "earliest_overdue_due_date": date(2026, 4, 1),
                "days_overdue": 14,
                "overdue_installment_count": 1,
                "overdue_regular_balance": Decimal("120.00"),
                "outstanding_late_charge_balance": Decimal("10.75"),
                "total_overdue_balance": Decimal("130.75"),
            }
        ]

        with patch(
            "app.api.routes.reports.list_overdue_loans",
            return_value=rows,
        ) as mock_list:
            result = list_overdue_loans_endpoint(
                date(2026, 4, 15), self.fake_db, self.current_user
            )

        self.assertEqual(result, rows)
        mock_list.assert_called_once_with(
            self.fake_db,
            as_of_date=date(2026, 4, 15),
            acting_user_id=self.current_user.id,
        )

    def test_list_recent_payments_returns_rows(self) -> None:
        rows = [
            {
                "id": uuid4(),
                "loan_id": uuid4(),
                "borrower_id": uuid4(),
                "recorded_by_user_id": uuid4(),
                "amount": Decimal("100.00"),
                "payment_date": date(2026, 4, 11),
                "recorded_at": "2026-04-11T12:00:00Z",
                "payment_method": "cash",
                "reference_code": "PMT-001",
                "notes": None,
                "is_backdated": False,
                "status": "recorded",
                "created_at": "2026-04-11T12:00:00Z",
                "updated_at": "2026-04-11T12:00:00Z",
                "allocations": [],
            }
        ]

        with patch(
            "app.api.routes.reports.list_recent_payments",
            return_value=rows,
        ) as mock_list:
            result = list_recent_payments_endpoint(10, self.fake_db, self.current_user)

        self.assertEqual(result, rows)
        mock_list.assert_called_once_with(self.fake_db, limit=10)

    def test_get_dashboard_summary_returns_summary(self) -> None:
        summary = {
            "active_loan_count": 2,
            "closed_loan_count": 1,
            "overdue_loan_count": 1,
            "total_outstanding_balance": Decimal("250.00"),
            "total_overdue_balance": Decimal("130.75"),
            "recent_payment_count": 3,
            "recent_payment_total": Decimal("180.00"),
        }

        with patch(
            "app.api.routes.reports.get_dashboard_summary",
            return_value=summary,
        ) as mock_summary:
            result = get_dashboard_summary_endpoint(
                date(2026, 4, 15), self.fake_db, self.current_user
            )

        self.assertEqual(result, summary)
        mock_summary.assert_called_once_with(
            self.fake_db,
            as_of_date=date(2026, 4, 15),
            acting_user_id=self.current_user.id,
        )


if __name__ == "__main__":
    unittest.main()
