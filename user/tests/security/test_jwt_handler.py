import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.security.jwt_handler import create_access_token, verify_token, SECRET_KEY, ALGORITHM


@pytest.fixture
def valid_payload():
    return {"sub": "testuser", "role": "admin"}


@pytest.fixture
def default_token(valid_payload):
    return create_access_token(valid_payload)


@pytest.fixture
def custom_expiry_token(valid_payload):
    expires = timedelta(hours=1)
    return create_access_token(valid_payload, expires_delta=expires)


def test_create_access_token_returns_string(default_token):
    assert isinstance(default_token, str)
    assert len(default_token) > 0


def test_create_access_token_default_expiry(default_token, valid_payload):
    decoded = jwt.decode(default_token, SECRET_KEY, algorithms=[ALGORITHM])
    for key, value in valid_payload.items():
        assert decoded[key] == value

    assert "exp" in decoded
    assert "iat" in decoded
    assert decoded["type"] == "access"

    exp_time = datetime.fromtimestamp(decoded["exp"])
    iat_time = datetime.fromtimestamp(decoded["iat"])
    delta = exp_time - iat_time
    assert 29.9 <= delta.total_seconds() / 60 <= 30.1


def test_create_access_token_custom_expiry(custom_expiry_token, valid_payload):
    decoded = jwt.decode(custom_expiry_token, SECRET_KEY, algorithms=[ALGORITHM])
    exp_time = datetime.fromtimestamp(decoded["exp"])
    iat_time = datetime.fromtimestamp(decoded["iat"])
    delta = exp_time - iat_time
    assert 59.9 <= delta.total_seconds() / 60 <= 60.1


def test_create_access_token_overrides_expires_delta(valid_payload):
    short = timedelta(minutes=5)
    token = create_access_token(valid_payload, expires_delta=short)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    iat = datetime.fromtimestamp(decoded["iat"])
    exp = datetime.fromtimestamp(decoded["exp"])
    delta = exp - iat
    assert 4.9 <= delta.total_seconds() / 60 <= 5.1


def test_verify_token_valid(default_token, valid_payload):
    payload = verify_token(default_token)
    assert payload["sub"] == valid_payload["sub"]
    assert payload["role"] == valid_payload["role"]
    assert "exp" in payload
    assert "iat" in payload
    assert payload["type"] == "access"


def test_verify_token_invalid_signature():
    token = create_access_token({"user": "test"})
    corrupted = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(HTTPException) as exc_info:
        verify_token(corrupted)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_verify_token_expired(valid_payload):
    expired_delta = timedelta(seconds=-1)
    token = create_access_token(valid_payload, expires_delta=expired_delta)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_verify_token_malformed():
    with pytest.raises(HTTPException) as exc_info:
        verify_token("not.a.token")
    assert exc_info.value.status_code == 401


def test_verify_token_missing_secret():
    try:
        token = create_access_token({"sub": "test"})
        with patch("src.security.jwt_handler.SECRET_KEY", "different_secret"):
            with pytest.raises(HTTPException):
                verify_token(token)
    finally:
        pass