from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.dependencies import get_current_user, require_admin_user  # noqa: E402
from app.models.user import User  # noqa: E402


class ApiDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = User(
            id=uuid4(),
            full_name="Admin User",
            email="admin@example.com",
            password_hash="hash",
            role="admin",
            is_active=True,
        )

    def test_get_current_user_returns_user_for_valid_token(self) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

        with patch(
            "app.api.dependencies.decode_access_token",
            return_value={"sub": str(self.user.id), "role": "admin"},
        ), patch(
            "app.api.dependencies.get_user_by_id",
            return_value=self.user,
        ):
            user = get_current_user(credentials, self.db)

        self.assertIs(user, self.user)

    def test_get_current_user_rejects_missing_credentials(self) -> None:
        with self.assertRaises(HTTPException) as exc_info:
            get_current_user(None, self.db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_current_user_rejects_invalid_token(self) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

        with patch(
            "app.api.dependencies.decode_access_token",
            side_effect=ValueError("bad token"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                get_current_user(credentials, self.db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_require_admin_user_rejects_staff(self) -> None:
        staff_user = User(
            id=uuid4(),
            full_name="Staff User",
            email="staff@example.com",
            password_hash="hash",
            role="staff",
            is_active=True,
        )

        with self.assertRaises(HTTPException) as exc_info:
            require_admin_user(staff_user)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_403_FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
