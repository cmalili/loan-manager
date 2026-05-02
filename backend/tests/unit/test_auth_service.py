from __future__ import annotations

import os
import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.core.security import (  # noqa: E402
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User  # noqa: E402
from app.services.auth import (  # noqa: E402
    AuthenticationError,
    InactiveUserError,
    authenticate_user,
    issue_access_token_for_user,
)


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = User(
            id=uuid4(),
            full_name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("secret-pass"),
            role="admin",
            is_active=True,
        )
        self.db = MagicMock()

    def test_hash_password_and_verify_password_round_trip(self) -> None:
        password_hash = hash_password("secret-pass")

        self.assertTrue(verify_password("secret-pass", password_hash))
        self.assertFalse(verify_password("wrong-pass", password_hash))

    def test_verify_password_rejects_malformed_hash(self) -> None:
        self.assertFalse(
            verify_password(
                "secret-pass",
                "pbkdf2_sha256$not-an-int$bad-salt$bad-hash",
            )
        )

    def test_create_and_decode_access_token_round_trip(self) -> None:
        token = create_access_token(
            subject=str(self.user.id),
            role=self.user.role,
            expires_delta=timedelta(minutes=5),
        )

        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], str(self.user.id))
        self.assertEqual(payload["role"], "admin")

    def test_authenticate_user_returns_user_for_valid_credentials(self) -> None:
        with patch("app.services.auth.get_user_by_email", return_value=self.user):
            user = authenticate_user(
                self.db,
                email="admin@example.com",
                password="secret-pass",
            )

        self.assertIs(user, self.user)

    def test_authenticate_user_rejects_invalid_credentials(self) -> None:
        with patch("app.services.auth.get_user_by_email", return_value=self.user):
            with self.assertRaisesRegex(AuthenticationError, "Invalid email or password"):
                authenticate_user(
                    self.db,
                    email="admin@example.com",
                    password="wrong-pass",
                )

    def test_authenticate_user_rejects_inactive_user(self) -> None:
        self.user.is_active = False

        with patch("app.services.auth.get_user_by_email", return_value=self.user):
            with self.assertRaisesRegex(InactiveUserError, "User account is inactive"):
                authenticate_user(
                    self.db,
                    email="admin@example.com",
                    password="secret-pass",
                )

    def test_issue_access_token_for_user_embeds_identity(self) -> None:
        token = issue_access_token_for_user(self.user)
        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], str(self.user.id))
        self.assertEqual(payload["role"], self.user.role)


if __name__ == "__main__":
    unittest.main()
