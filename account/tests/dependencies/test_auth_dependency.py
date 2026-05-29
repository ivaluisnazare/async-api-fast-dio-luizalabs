import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.dependencies.auth_dependency import get_current_user, get_current_user_id, require_same_user

@pytest.fixture
def mock_storage():
    with patch("src.dependencies.auth_dependency.storage") as mock:
        yield mock


@pytest.fixture
def mock_validator_factory():
    """Mock the get_token_validator function, returning an async validator."""
    with patch("src.dependencies.auth_dependency.get_token_validator") as mock:
        validator = AsyncMock()
        mock.return_value = validator
        yield validator


@pytest.mark.asyncio
async def test_get_current_user_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Missing authentication credentials"


@pytest.mark.asyncio
async def test_get_current_user_token_in_storage(mock_storage):
    mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    mock_credentials.credentials = "test-token"

    mock_storage.get_token_info.return_value = {
        "user_id": 123,
        "username": "john_doe",
        "token_type": "bearer",
    }

    result = await get_current_user(credentials=mock_credentials)

    mock_storage.get_token_info.assert_called_once_with("test-token")
    assert result == {
        "user_id": 123,
        "username": "john_doe",
        "token_type": "bearer",
        "source": "rabbitmq_storage",
    }


@pytest.mark.asyncio
async def test_get_current_user_token_not_in_storage_valid_jwt(mock_storage, mock_validator_factory):
    mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    mock_credentials.credentials = "jwt-token"

    mock_storage.get_token_info.return_value = None

    expected_payload = {
        "user_id": 456,
        "username": "jane_doe",
        "email": "jane@example.com",
    }
    mock_validator_factory.validate_token = AsyncMock(return_value=expected_payload)

    result = await get_current_user(credentials=mock_credentials)

    mock_validator_factory.validate_token.assert_called_once_with("jwt-token")
    assert result == {
        "user_id": 456,
        "username": "jane_doe",
        "email": "jane@example.com",
        "source": "jwt_validation",
    }


@pytest.mark.asyncio
async def test_get_current_user_jwt_validation_http_exception(mock_storage, mock_validator_factory):
    mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    mock_credentials.credentials = "invalid-token"

    mock_storage.get_token_info.return_value = None

    # Simulate HTTPException from validator
    http_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    mock_validator_factory.validate_token = AsyncMock(side_effect=http_exc)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials)

    assert exc_info.value == http_exc


@pytest.mark.asyncio
async def test_get_current_user_jwt_validation_unexpected_exception(mock_storage, mock_validator_factory):
    mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    mock_credentials.credentials = "bad-token"

    mock_storage.get_token_info.return_value = None

    mock_validator_factory.validate_token = AsyncMock(side_effect=RuntimeError("Something went wrong"))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid authentication credentials"


def test_get_current_user_id():
    current_user = {"user_id": 789, "username": "test_user"}
    result = get_current_user_id(current_user=current_user)
    assert result == 789


@pytest.mark.asyncio
async def test_require_same_user_success():
    current_user = {"user_id": 999, "username": "owner"}
    result = await require_same_user(user_id=999, current_user=current_user)
    assert result == current_user


@pytest.mark.asyncio
async def test_require_same_user_forbidden():
    current_user = {"user_id": 888, "username": "other"}
    with pytest.raises(HTTPException) as exc_info:
        await require_same_user(user_id=777, current_user=current_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Not authorized to access this resource"