from __future__ import annotations

import os
import unittest
from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException, status

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.api.routes.auth import login_endpoint  # noqa: E402
from app.schemas.auth import LoginRequest  # noqa: E402
from app.services.auth import (  # noqa: E402
    AuthenticationError,
    InactiveUserError,
)


class AuthRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_db = object()
        self.user = {
            "id": uuid4(),
            "full_name": "Admin User",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True,
            "created_at": "2026-04-14T12:00:00Z",
            "updated_at": "2026-04-14T12:00:00Z",
        }

    def test_login_returns_token_and_user(self) -> None:
        payload = LoginRequest(email="admin@example.com", password="secret-pass")

        with patch(
            "app.api.routes.auth.authenticate_user",
            return_value=self.user,
        ) as mock_authenticate, patch(
            "app.api.routes.auth.issue_access_token_for_user",
            return_value="signed-token",
        ) as mock_issue:
            result = login_endpoint(payload, self.fake_db)

        self.assertEqual(result.access_token, "signed-token")
        self.assertEqual(result.user.email, "admin@example.com")
        mock_authenticate.assert_called_once_with(
            self.fake_db, email="admin@example.com", password="secret-pass"
        )
        mock_issue.assert_called_once_with(self.user)

    def test_login_returns_401_on_invalid_credentials(self) -> None:
        payload = LoginRequest(email="admin@example.com", password="wrong-pass")

        with patch(
            "app.api.routes.auth.authenticate_user",
            side_effect=AuthenticationError("Invalid email or password"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                login_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(exc_info.exception.detail, "Invalid email or password")

    def test_login_returns_401_on_inactive_user(self) -> None:
        payload = LoginRequest(email="admin@example.com", password="secret-pass")

        with patch(
            "app.api.routes.auth.authenticate_user",
            side_effect=InactiveUserError("User account is inactive"),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                login_endpoint(payload, self.fake_db)

        self.assertEqual(exc_info.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(exc_info.exception.detail, "User account is inactive")


if __name__ == "__main__":
    unittest.main()
