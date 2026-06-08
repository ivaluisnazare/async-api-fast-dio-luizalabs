from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status

from src.exceptions.custom_exceptions import (
    DuplicateUserException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from src.schemas.users import Token, UserCreate, UserResponse


class TestUserController:

    @pytest.mark.asyncio
    async def test_get_all_users_success(
        self, async_client, mock_db_session, sample_user_data
    ):
        # Arrange
        sample_user_response = UserResponse.model_validate(sample_user_data)

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_users = AsyncMock(return_value=[sample_user_response])
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["username"] == sample_user_data["username"]
            mock_service.get_all_users.assert_called_once_with(skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_get_all_users_with_pagination(
        self, async_client, mock_db_session, sample_user_data
    ):
        # Arrange
        sample_user_response = UserResponse.model_validate(sample_user_data)

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_users = AsyncMock(return_value=[sample_user_response])
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/?skip=10&limit=50")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.get_all_users.assert_called_once_with(skip=10, limit=50)

    @pytest.mark.asyncio
    async def test_get_all_users_server_error(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_users = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/")

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Database error"

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, async_client, mock_db_session, sample_user_data
    ):
        # Arrange
        sample_user_response = UserResponse.model_validate(sample_user_data)

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_by_id = AsyncMock(return_value=sample_user_response)
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/1")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == sample_user_data["id"]
            assert data["username"] == sample_user_data["username"]
            mock_service.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_by_id = AsyncMock(
                side_effect=UserNotFoundException("User not found")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/999")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert (
                response.json()["detail"]
                == "404: User with id User not found not found"
            )

    @pytest.mark.asyncio
    async def test_get_user_by_id_server_error(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_by_id = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.get("/users/1")

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Database error"

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, async_client, mock_db_session, sample_user_data
    ):
        # Arrange
        sample_user_response = UserResponse.model_validate(sample_user_data)
        user_create_data = {
            "username": "newuser",
            "email": "new@example.com",
            "full_name": "New User",
            "password": "password123",
        }

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user = AsyncMock(return_value=sample_user_response)
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.post("/users/", json=user_create_data)

            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["username"] == sample_user_data["username"]
            assert "password" not in data
            mock_service.create_user.assert_called_once()

            call_args = mock_service.create_user.call_args[0][0]
            assert isinstance(call_args, UserCreate)
            assert call_args.username == user_create_data["username"]

    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, async_client, mock_db_session):
        # Arrange
        user_create_data = {
            "username": "existinguser",
            "email": "existing@example.com",
            "full_name": "Existing User",
            "password": "password123",
        }

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user = AsyncMock(
                side_effect=DuplicateUserException("Username already exists")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.post("/users/", json=user_create_data)

            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert (
                response.json()["detail"]
                == "409: User with username Username already exists already exists"
            )

    @pytest.mark.asyncio
    async def test_create_user_validation_error(self, async_client):
        # Arrange
        invalid_user_data = {
            "username": "ab",
            "email": "invalid-email",
            "password": "123",
        }

        # Act
        response = await async_client.post("/users/", json=invalid_user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_server_error(self, async_client, mock_db_session):
        # Arrange
        user_create_data = {
            "username": "newuser",
            "email": "new@example.com",
            "full_name": "New User",
            "password": "password123",
        }

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.post("/users/", json=user_create_data)

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Database error"

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, async_client, mock_db_session, sample_user_data
    ):
        # Arrange
        sample_user_response = UserResponse.model_validate(sample_user_data)
        update_data = {"email": "updated@example.com", "full_name": "Updated User"}

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user = AsyncMock(return_value=sample_user_response)
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.put("/users/1", json=update_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.update_user.assert_called_once_with(
                1, mock_service.update_user.call_args[0][1]
            )

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client, mock_db_session):
        # Arrange
        update_data = {"email": "updated@example.com", "full_name": "Updated User"}

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user = AsyncMock(
                side_effect=UserNotFoundException("User not found")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.put("/users/999", json=update_data)

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert (
                response.json()["detail"]
                == "404: User with id User not found not found"
            )

    @pytest.mark.asyncio
    async def test_update_user_server_error(self, async_client, mock_db_session):
        # Arrange
        update_data = {"email": "updated@example.com", "full_name": "Updated User"}

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.put("/users/1", json=update_data)

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Database error"

    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.delete_user = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.delete("/users/1")

            # Assert
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_service.delete_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.delete_user = AsyncMock(
                side_effect=UserNotFoundException("User not found")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.delete("/users/999")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert (
                response.json()["detail"]
                == "404: User with id User not found not found"
            )

    @pytest.mark.asyncio
    async def test_delete_user_server_error(self, async_client, mock_db_session):
        # Arrange
        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch(
            "src.controller.user_controller.UserService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.delete_user = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            # Act
            response = await async_client.delete("/users/1")

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Database error"

    @pytest.mark.asyncio
    async def test_login_success(self, async_client, mock_db_session):
        # Arrange
        login_data = {"username": "testuser", "password": "password123"}

        token_response = {
            "access_token": "mock_jwt_token",
            "token_type": "bearer",
            "user_id": 1,
            "username": "testuser",
            "expires_in": 1800,
        }

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch("src.controller.user_controller.AuthService") as mock_auth_class:
            mock_auth_service = AsyncMock()
            mock_auth_service.login = AsyncMock(return_value=Token(**token_response))
            mock_auth_class.return_value = mock_auth_service

            # Act
            response = await async_client.post("/users/login", json=login_data)

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == token_response["access_token"]
            assert data["token_type"] == token_response["token_type"]
            assert data["user_id"] == token_response["user_id"]
            mock_auth_service.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client, mock_db_session):
        # Arrange
        login_data = {"username": "testuser", "password": "wrongpassword"}

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch("src.controller.user_controller.AuthService") as mock_auth_class:
            mock_auth_service = AsyncMock()
            mock_auth_service.login = AsyncMock(
                side_effect=InvalidCredentialsException()
            )
            mock_auth_class.return_value = mock_auth_service

            # Act
            response = await async_client.post("/users/login", json=login_data)

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_server_error(self, async_client, mock_db_session):
        # Arrange
        login_data = {"username": "testuser", "password": "password123"}

        with patch(
            "src.controller.user_controller.get_db", return_value=mock_db_session
        ), patch("src.controller.user_controller.AuthService") as mock_auth_class:
            mock_auth_service = AsyncMock()
            mock_auth_service.login = AsyncMock(
                side_effect=Exception("Authentication error")
            )
            mock_auth_class.return_value = mock_auth_service

            # Act
            response = await async_client.post("/users/login", json=login_data)

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"] == "Authentication error"

    @pytest.mark.asyncio
    async def test_login_validation_error(self, async_client):
        # Arrange
        invalid_login_data = {}

        # Act
        response = await async_client.post("/users/login", json=invalid_login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_invalid_username_format(self, async_client):
        # Arrange
        invalid_login_data = {"username": "ab", "password": "password123"}

        # Act
        response = await async_client.post("/users/login", json=invalid_login_data)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
