import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from user.src.main import app
from user.src.repository.user_repository import UserRepository
from user.src.schemas.user import UserCreate, UserResponse, UserUpdate
from user.src.service.user_service import UserService

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest_asyncio.fixture(scope="session")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def event_loop():
    """Fixture para event loop do asyncio"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
def mock_db_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def sample_user_data():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "password": "hashed_password",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def sample_user_create():
    return UserCreate(
        username="newuser",
        email="new@example.com",
        full_name="New User",
        password="password123",
    )


@pytest.fixture
def sample_user_update():
    return UserUpdate(
        email="updated@example.com", full_name="Updated User", is_active=False
    )


@pytest.fixture
def sample_user_response(sample_user_data):
    return UserResponse.model_validate(sample_user_data)


@pytest_asyncio.fixture
async def user_service_with_mock_repo(mock_db_session):
    mock_repository = AsyncMock(spec=UserRepository)

    mock_repository.get_all = AsyncMock(return_value=[])
    mock_repository.get_by_id = AsyncMock()
    mock_repository.get_by_username = AsyncMock()
    mock_repository.create = AsyncMock()
    mock_repository.update = AsyncMock()
    mock_repository.delete = AsyncMock()

    with patch(
        "user.src.service.user_service.UserRepository", return_value=mock_repository
    ):
        service = UserService(mock_db_session)
        service.repository = mock_repository
        yield service, mock_repository


@pytest.fixture
def mock_jwt_handler():
    with patch("user.src.service.user_service.get_password_hash") as mock_hash:
        mock_hash.return_value = "hashed_password"
        yield mock_hash
