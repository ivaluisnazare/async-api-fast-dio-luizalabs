import pytest
import pytest_asyncio
import sys
import os
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from account.main import app
from shared.database import get_db
from account.src.dependencies.auth_dependency import get_current_user, get_current_user_id


@pytest_asyncio.fixture
async def mock_db_session():
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest_asyncio.fixture
async def client(mock_db_session) -> AsyncGenerator[AsyncClient, None]:

    async def override_get_db():
        yield mock_db_session

    mock_user = {
        "user_id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "source": "jwt_validation"
    }

    async def override_get_current_user():
        return mock_user

    async def override_get_current_user_id():
        return 1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer mock_token_12345"
    }