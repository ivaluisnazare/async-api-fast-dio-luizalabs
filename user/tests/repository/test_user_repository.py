import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.user_repository import UserRepository  # Ajuste o import se necessário
from src.schemas.users import UserCreate, UserUpdate
from src.exceptions.custom_exceptions import (
    DuplicateUserException,
    InactiveUserException,
    InvalidCredentialsException,
    UserNotFoundException,
)

FAKE_USER_DATA = {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "password": "hashed_password_123",
    "full_name": "Test User",
    "is_active": True,
}


@pytest.fixture
def mock_db_session():
    """Fixture que cria um mock asíncrono para a sessão do banco de dados."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_db_session):
    """Fixture que instancia o repositório injetando o mock do banco."""
    return UserRepository(db=mock_db_session)


@pytest.mark.asyncio
class TestUserRepository:

    # --- TESTES DE GET_ALL ---

    async def test_get_all_success(self, repository, mock_db_session):
        # Mocking o resultado do banco
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = FAKE_USER_DATA
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result

        users = await repository.get_all(skip=0, limit=10)

        assert len(users) == 1
        assert users[0]["username"] == "testuser"
        mock_db_session.execute.assert_called_once()

    # --- TESTES DE GET_BY_ID ---

    async def test_get_by_id_success(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = FAKE_USER_DATA
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        user = await repository.get_by_id(1)

        assert user["id"] == 1
        assert user["email"] == "test@example.com"

    async def test_get_by_id_not_found(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(UserNotFoundException):
            await repository.get_by_id(999)

    # --- TESTES DE GET_BY_USERNAME ---

    async def test_get_by_username_success(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = FAKE_USER_DATA
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        user = await repository.get_by_username("testuser")

        assert user["username"] == "testuser"

    async def test_get_by_username_not_found(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(UserNotFoundException):
            await repository.get_by_username("nonexistent")

    # --- TESTES DE GET_BY_EMAIL ---

    async def test_get_by_email_success(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = FAKE_USER_DATA
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        user = await repository.get_by_email("test@example.com")

        assert user["email"] == "test@example.com"

    async def test_get_by_email_not_found(self, repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(UserNotFoundException):
            await repository.get_by_email("wrong@example.com")

    # --- TESTES DE CREATE ---

    async def test_create_user_success(self, repository, mock_db_session):
        user_create = UserCreate(username="newuser", email="new@example.com", password="password125",
                                 full_name="New User")

        # Simular que get_by_username e get_by_email NÃO encontram ninguém (lançam UserNotFoundException)
        with patch.object(repository, 'get_by_username', side_effect=UserNotFoundException), \
                patch.object(repository, 'get_by_email', side_effect=UserNotFoundException):
            mock_result = MagicMock()
            mock_row = MagicMock()
            mock_row._mapping = {**FAKE_USER_DATA, "username": "newuser", "email": "new@example.com"}
            mock_result.fetchone.return_value = mock_row
            mock_db_session.execute.return_value = mock_result

            created_user = await repository.create(user_create, "hashed_new_password")

            assert created_user["username"] == "newuser"
            assert created_user["email"] == "new@example.com"

    async def test_create_user_duplicate_username(self, repository):
        user_create = UserCreate(username="testuser", email="new@example.com", password="password125",
                                 full_name="New User")

        # Simular que o username já existe
        with patch.object(repository, 'get_by_username', return_value=FAKE_USER_DATA):
            with pytest.raises(DuplicateUserException) as exc_info:
                await repository.create(user_create, "hashed_password")
            assert "username" in str(exc_info.value.__dict__)

    async def test_create_user_duplicate_email(self, repository):
        user_create = UserCreate(username="newuser", email="test@example.com", password="password125",
                                 full_name="New User")

        # Simular que username está livre, mas o email já existe
        with patch.object(repository, 'get_by_username', side_effect=UserNotFoundException), \
                patch.object(repository, 'get_by_email', return_value=FAKE_USER_DATA):
            with pytest.raises(DuplicateUserException) as exc_info:
                await repository.create(user_create, "hashed_password")
            assert "email" in str(exc_info.value.__dict__)

    # --- TESTES DE UPDATE ---

    async def test_update_user_success(self, repository, mock_db_session):
        user_update = UserUpdate(full_name="Updated Name")

        with patch.object(repository, 'get_by_id', return_value=FAKE_USER_DATA):
            mock_result = MagicMock()
            mock_row = MagicMock()
            mock_row._mapping = {**FAKE_USER_DATA, "full_name": "Updated Name"}
            mock_result.fetchone.return_value = mock_row
            mock_db_session.execute.return_value = mock_result

            updated_user = await repository.update(1, user_update)
            assert updated_user["full_name"] == "Updated Name"

    async def test_update_user_no_changes(self, repository):
        # Se os dados enviados forem vazios, deve apenas retornar o usuário atual sem rodar query de update
        user_update = UserUpdate()

        with patch.object(repository, 'get_by_id', return_value=FAKE_USER_DATA) as mock_get_by_id:
            updated_user = await repository.update(1, user_update)
            assert updated_user == FAKE_USER_DATA
            assert mock_get_by_id.call_count == 2  # Chamado no início e no retorno precoce

    async def test_update_user_not_found_on_execution(self, repository, mock_db_session):
        user_update = UserUpdate(full_name="Updated Name")

        # Passa pelo primeiro get_by_id, mas a query de update retorna vazia por alguma anomalia concorrente
        with patch.object(repository, 'get_by_id', return_value=FAKE_USER_DATA):
            mock_result = MagicMock()
            mock_result.fetchone.return_value = None
            mock_db_session.execute.return_value = mock_result

            with pytest.raises(UserNotFoundException):
                await repository.update(1, user_update)

    # --- TESTES DE DELETE ---

    async def test_delete_user_success(self, repository, mock_db_session):
        with patch.object(repository, 'get_by_id', return_value=FAKE_USER_DATA):
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_db_session.execute.return_value = mock_result

            result = await repository.delete(1)
            assert result is True

    # --- TESTES DE AUTHENTICATE_USER ---

    @patch("src.security.jwt_handler.verify_password")
    async def test_authenticate_user_success(self, mock_verify_password, repository):
        mock_verify_password.return_value = True

        with patch.object(repository, 'get_by_username', return_value=FAKE_USER_DATA):
            user = await repository.authenticate_user("testuser", "correct_password")
            assert user == FAKE_USER_DATA

    @patch("src.security.jwt_handler.verify_password")
    async def test_authenticate_user_wrong_password(self, mock_verify_password, repository):
        mock_verify_password.return_value = False

        with patch.object(repository, 'get_by_username', return_value=FAKE_USER_DATA):
            with pytest.raises(InvalidCredentialsException):
                await repository.authenticate_user("testuser", "wrong_password")

    async def test_authenticate_user_not_found(self, repository):
        with patch.object(repository, 'get_by_username', side_effect=UserNotFoundException):
            with pytest.raises(InvalidCredentialsException):
                await repository.authenticate_user("nonexistent", "any_password")

    @patch("src.security.jwt_handler.verify_password")
    async def test_authenticate_user_inactive(self, mock_verify_password, repository):
        mock_verify_password.return_value = True
        inactive_user = {**FAKE_USER_DATA, "is_active": False}

        with patch.object(repository, 'get_by_username', return_value=inactive_user):
            with pytest.raises(InactiveUserException):
                await repository.authenticate_user("testuser", "correct_password")