"""Authentication and password security helpers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


PBKDF2_ITERATIONS = 100_000


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256."""

    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{_b64url_encode(salt)}${_b64url_encode(derived_key)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""

    try:
        algorithm, iterations_text, salt_text, hash_text = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
        salt = _b64url_decode(salt_text)
        expected_hash = _b64url_decode(hash_text)
    except (ValueError, binascii.Error):
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_hash, expected_hash)


def create_access_token(
    *,
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed bearer token with an expiry timestamp."""

    now = datetime.now(timezone.utc)
    expiry = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": subject,
        "role": role,
        "exp": int(expiry.timestamp()),
    }
    payload_segment = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{payload_segment}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, object]:
    """Validate and decode a signed bearer token."""

    try:
        payload_segment, signature_segment = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed access token") from exc

    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_segment)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise ValueError("Invalid access token signature")

    payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    expiry = int(payload["exp"])
    if datetime.now(timezone.utc).timestamp() >= expiry:
        raise ValueError("Access token has expired")
    return payload
