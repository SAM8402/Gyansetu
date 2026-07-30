from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify_matches(self):
        hashed = hash_password("my_secure_password")
        assert verify_password("my_secure_password", hashed) is True

    def test_verify_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_different_each_time(self):
        pw = "same_password"
        assert hash_password(pw) != hash_password(pw)

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False


class TestAccessToken:
    def test_create_and_decode(self):
        token = create_access_token("user-123", "teacher")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "teacher"
        assert payload["type"] == "access"

    def test_token_has_expiry(self):
        token = create_access_token("user-1", "admin")
        payload = decode_token(token)
        assert "exp" in payload

    def test_expired_token_returns_none(self):
        expired_token = jwt.encode(
            {
                "sub": "user-1",
                "role": "teacher",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                "type": "access",
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        assert decode_token(expired_token) is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user-1", "teacher")
        parts = token.rsplit(".", 1)
        tampered = parts[0] + ".invalidsignature"
        assert decode_token(tampered) is None

    def test_wrong_secret_returns_none(self):
        token = jwt.encode(
            {"sub": "u1", "role": "teacher", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "type": "access"},
            "different-secret",
            algorithm="HS256",
        )
        assert decode_token(token) is None


class TestRefreshToken:
    def test_create_and_decode(self):
        token = create_refresh_token("user-456")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_refresh_no_role_claim(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert "role" not in payload

    def test_access_and_refresh_are_different(self):
        access = create_access_token("u1", "teacher")
        refresh = create_refresh_token("u1")
        assert access != refresh
