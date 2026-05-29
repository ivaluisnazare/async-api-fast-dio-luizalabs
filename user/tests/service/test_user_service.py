from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.custom_exceptions import (DuplicateUserException,
                                                   UserNotFoundException)
from src.schemas.users import UserCreate, UserResponse, UserUpdate
from src.service.user_service import UserService


@pytest.mark.asyncio
class TestUserService:

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_user_data(self):
        return {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "password": "hashed_password",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    @pytest.fixture
    def user_create_data(self):
        return UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="New User",
            password="password123",
        )

    @pytest.fixture
    def user_update_data(self):
        return UserUpdate(
            email="updated@example.com", full_name="Updated User", is_active=False
        )

    async def test_get_all_users_success(self, mock_db_session, mock_user_data):
        # Mock do repositório
        mock_repository = AsyncMock()
        mock_repository.get_all = AsyncMock(return_value=[mock_user_data])

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.get_all_users(skip=0, limit=10)

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], UserResponse)
            assert result[0].id == mock_user_data["id"]
            assert result[0].username == mock_user_data["username"]
            mock_repository.get_all.assert_called_once_with(0, 10)

    async def test_get_all_users_empty(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.get_all = AsyncMock(return_value=[])

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.get_all_users()

            assert isinstance(result, list)
            assert len(result) == 0
            mock_repository.get_all.assert_called_once()

    async def test_get_user_by_id_success(self, mock_db_session, mock_user_data):
        mock_repository = AsyncMock()
        mock_repository.get_by_id = AsyncMock(return_value=mock_user_data)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.get_user_by_id(user_id=1)

            assert isinstance(result, UserResponse)
            assert result.id == mock_user_data["id"]
            assert result.username == mock_user_data["username"]
            mock_repository.get_by_id.assert_called_once_with(1)

    async def test_get_user_by_id_not_found(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.get_by_id = AsyncMock(
            side_effect=UserNotFoundException(user_id=1)
        )

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            with pytest.raises(UserNotFoundException):
                await service.get_user_by_id(user_id=1)

            mock_repository.get_by_id.assert_called_once_with(1)

    async def test_get_user_by_username_success(self, mock_db_session, mock_user_data):
        mock_repository = AsyncMock()
        mock_repository.get_by_username = AsyncMock(return_value=mock_user_data)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.get_user_by_username(username="testuser")

            assert isinstance(result, UserResponse)
            assert result.username == "testuser"
            mock_repository.get_by_username.assert_called_once_with("testuser")

    async def test_get_user_by_username_not_found(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.get_by_username = AsyncMock(
            side_effect=UserNotFoundException(username="nonexistent")
        )

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            with pytest.raises(UserNotFoundException):
                await service.get_user_by_username(username="nonexistent")

            mock_repository.get_by_username.assert_called_once_with("nonexistent")

    async def test_create_user_success(
        self, mock_db_session, mock_user_data, user_create_data
    ):
        # Mock
        with patch(
            "src.service.user_service.get_password_hash",
            return_value="hashed_password",
        ):
            mock_repository = AsyncMock()
            mock_repository.create = AsyncMock(return_value=mock_user_data)

            with patch(
                "src.service.user_service.UserRepository",
                return_value=mock_repository,
            ):
                service = UserService(mock_db_session)

                result = await service.create_user(user_create_data)

                assert isinstance(result, UserResponse)
                assert result.username == user_create_data.username
                assert result.email == user_create_data.email
                mock_repository.create.assert_called_once_with(
                    user_create_data, "hashed_password"
                )
                mock_db_session.commit.assert_called_once()

    async def test_create_user_duplicate_username(
        self, mock_db_session, user_create_data
    ):
        with patch(
            "src.service.user_service.get_password_hash",
            return_value="hashed_password",
        ):
            mock_repository = AsyncMock()
            mock_repository.create = AsyncMock(
                side_effect=DuplicateUserException(username=user_create_data.username)
            )

            with patch(
                "src.service.user_service.UserRepository",
                return_value=mock_repository,
            ):
                service = UserService(mock_db_session)

                with pytest.raises(DuplicateUserException):
                    await service.create_user(user_create_data)

                mock_repository.create.assert_called_once()
                mock_db_session.rollback.assert_called_once()

    async def test_create_user_exception_rollback(
        self, mock_db_session, user_create_data
    ):
        with patch(
            "src.service.user_service.get_password_hash",
            return_value="hashed_password",
        ):
            mock_repository = AsyncMock()
            mock_repository.create = AsyncMock(side_effect=Exception("Database error"))

            with patch(
                "src.service.user_service.UserRepository",
                return_value=mock_repository,
            ):
                service = UserService(mock_db_session)

                with pytest.raises(Exception):
                    await service.create_user(user_create_data)

                mock_repository.create.assert_called_once()
                mock_db_session.rollback.assert_called_once()

    async def test_update_user_success(
        self, mock_db_session, mock_user_data, user_update_data
    ):
        updated_data = {**mock_user_data, "email": "updated@example.com"}
        mock_repository = AsyncMock()
        mock_repository.update = AsyncMock(return_value=updated_data)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.update_user(user_id=1, user_data=user_update_data)

            assert isinstance(result, UserResponse)
            assert result.email == "updated@example.com"
            mock_repository.update.assert_called_once_with(1, user_update_data)
            mock_db_session.commit.assert_called_once()

    async def test_update_user_not_found(self, mock_db_session, user_update_data):
        mock_repository = AsyncMock()
        mock_repository.update = AsyncMock(
            side_effect=UserNotFoundException(user_id=999)
        )

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            with pytest.raises(UserNotFoundException):
                await service.update_user(user_id=999, user_data=user_update_data)

            mock_repository.update.assert_called_once_with(999, user_update_data)
            mock_db_session.rollback.assert_called_once()

    async def test_update_user_empty_data(self, mock_db_session, mock_user_data):
        user_update_empty = UserUpdate()
        mock_repository = AsyncMock()
        mock_repository.update = AsyncMock(return_value=mock_user_data)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.update_user(user_id=1, user_data=user_update_empty)

            assert isinstance(result, UserResponse)
            mock_repository.update.assert_called_once_with(1, user_update_empty)

    async def test_delete_user_success(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.delete = AsyncMock(return_value=True)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.delete_user(user_id=1)

            assert result is True
            mock_repository.delete.assert_called_once_with(1)
            mock_db_session.commit.assert_called_once()

    async def test_delete_user_not_found(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.delete = AsyncMock(
            side_effect=UserNotFoundException(user_id=999)
        )

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            with pytest.raises(UserNotFoundException):
                await service.delete_user(user_id=999)

            mock_repository.delete.assert_called_once_with(999)
            mock_db_session.rollback.assert_called_once()

    async def test_delete_user_failure(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.delete = AsyncMock(return_value=False)

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.delete_user(user_id=1)

            assert result is False
            mock_repository.delete.assert_called_once_with(1)

    async def test_delete_user_exception_rollback(self, mock_db_session):
        mock_repository = AsyncMock()
        mock_repository.delete = AsyncMock(side_effect=Exception("Database error"))

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            with pytest.raises(Exception):
                await service.delete_user(user_id=1)

            mock_repository.delete.assert_called_once_with(1)
            mock_db_session.rollback.assert_called_once()

    async def test_user_response_model_validation(self, mock_user_data):
        # Test
        user_response = UserResponse.model_validate(mock_user_data)
        assert user_response.id == mock_user_data["id"]
        assert user_response.username == mock_user_data["username"]
        assert user_response.email == mock_user_data["email"]
        assert user_response.is_active == mock_user_data["is_active"]

        invalid_data = mock_user_data.copy()
        del invalid_data["id"]

        with pytest.raises(ValueError):
            UserResponse.model_validate(invalid_data)

    @pytest.mark.parametrize("skip,limit", [(0, 10), (10, 20), (0, 100)])
    async def test_get_all_users_with_different_params(
        self, mock_db_session, skip, limit
    ):
        mock_repository = AsyncMock()
        mock_repository.get_all = AsyncMock(return_value=[])

        with patch(
            "src.service.user_service.UserRepository", return_value=mock_repository
        ):
            service = UserService(mock_db_session)

            result = await service.get_all_users(skip=skip, limit=limit)

            assert isinstance(result, list)
            mock_repository.get_all.assert_called_once_with(skip, limit)
