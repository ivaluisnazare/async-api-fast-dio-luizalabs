# test_account_repository.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from account.src.models.account import accounts
from account.src.schemas.account import AccountCreate, AccountUpdate
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    DuplicateAccountException
)
from account.src.repository.account_repository import AccountRepository


@pytest.fixture
def mock_db():
    """Fixture para mock do banco de dados"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def account_repository(mock_db):
    """Fixture para o repositório"""
    return AccountRepository(mock_db)


@pytest.fixture
def sample_account_data():
    """Dados de exemplo para uma conta"""
    return {
        "id": 1,
        "user_id": 123,
        "balance": Decimal("1000.00"),
        "created_at": "2023-01-01T00:00:00"
    }


@pytest.fixture
def sample_account_create():
    """Fixture para AccountCreate"""
    return AccountCreate(user_id=123, balance=Decimal("1000.00"))


@pytest.fixture
def sample_account_update():
    """Fixture para AccountUpdate"""
    return AccountUpdate(balance=Decimal("1500.00"))


class TestAccountRepository:
    """Testes para AccountRepository"""

    @pytest.mark.asyncio
    async def test_get_all_success(self, account_repository, mock_db, sample_account_data):
        """Testa busca de todas as contas com sucesso"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(_mapping=sample_account_data)
        ]
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.get_all(skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_account_data
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_empty(self, account_repository, mock_db):
        """Testa busca de todas as contas quando não há dados"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.get_all()

        # Assert
        assert result == []
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, account_repository, mock_db, sample_account_data):
        """Testa busca de conta por ID com sucesso"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.get_by_id(account_id=1)

        # Assert
        assert result == sample_account_data
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, account_repository, mock_db):
        """Testa busca de conta por ID quando não encontrada"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException) as exc_info:
            await account_repository.get_by_id(account_id=999)

        assert "Account with id 999 not found" in str(exc_info.value)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_id_success(self, account_repository, mock_db, sample_account_data):
        """Testa busca de conta por user_id com sucesso"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.get_by_user_id(user_id=123)

        # Assert
        assert result == sample_account_data
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_id_not_found(self, account_repository, mock_db):
        """Testa busca de conta por user_id quando não encontrada"""
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException) as exc_info:
            await account_repository.get_by_user_id(user_id=999)

        assert "Account for user 999 not found" in str(exc_info.value)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_success(self, account_repository, mock_db, sample_account_create, sample_account_data):
        """Testa criação de conta com sucesso"""
        # Arrange
        # Mock para get_by_user_id (lança exceção indicando que conta não existe)
        account_repository.get_by_user_id = AsyncMock(side_effect=AccountNotFoundException(user_id=123))

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.create(account_data=sample_account_create)

        # Assert
        assert result == sample_account_data
        mock_db.execute.assert_called_once()
        account_repository.get_by_user_id.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_create_duplicate_account(self, account_repository, sample_account_create, sample_account_data):
        """Testa criação de conta duplicada"""
        # Arrange
        # Mock para get_by_user_id (retorna conta existente)
        account_repository.get_by_user_id = AsyncMock(return_value=sample_account_data)

        # Act & Assert
        with pytest.raises(DuplicateAccountException) as exc_info:
            await account_repository.create(account_data=sample_account_create)

        assert "Account for user 123 already exists" in str(exc_info.value)
        account_repository.get_by_user_id.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_update_success(self, account_repository, mock_db, sample_account_data, sample_account_update):
        """Testa atualização de conta com sucesso"""
        # Arrange
        # Mock para get_by_id
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping={**sample_account_data, "balance": Decimal("1500.00")})
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.update(account_id=1, account_data=sample_account_update)

        # Assert
        assert result["balance"] == Decimal("1500.00")
        account_repository.get_by_id.assert_called_once_with(1)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_no_changes(self, account_repository, sample_account_data, sample_account_update):
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        empty_update_data = AccountUpdate()

        # Act
        result = await account_repository.update(account_id=1, account_data=empty_update_data)

        # Assert
        assert result == sample_account_data

    @pytest.mark.asyncio
    async def test_update_account_not_found(self, account_repository, sample_account_update):
        # Arrange
        account_repository.get_by_id = AsyncMock(side_effect=AccountNotFoundException(account_id=999))

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_repository.update(account_id=999, account_data=sample_account_update)

        account_repository.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_delete_success(self, account_repository, mock_db, sample_account_data):
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.delete(account_id=1)

        # Assert
        assert result is True
        account_repository.get_by_id.assert_called_once_with(1)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, account_repository):
        """Testa exclusão de conta não encontrada"""
        # Arrange
        account_repository.get_by_id = AsyncMock(side_effect=AccountNotFoundException(account_id=999))

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_repository.delete(account_id=999)

        account_repository.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_delete_no_rows_affected(self, account_repository, mock_db, sample_account_data):
        """Testa exclusão quando nenhuma linha é afetada"""
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.delete(account_id=1)

        # Assert
        assert result is False
        account_repository.get_by_id.assert_called_once_with(1)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_balance_success(self, account_repository, mock_db, sample_account_data):
        """Testa atualização de saldo com sucesso"""
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        new_balance = Decimal("2000.00")
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping={**sample_account_data, "balance": new_balance})
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.update_balance(account_id=1, new_balance=new_balance)

        # Assert
        assert result["balance"] == new_balance
        account_repository.get_by_id.assert_called_once_with(1)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_balance_not_found(self, account_repository):
        """Testa atualização de saldo para conta não encontrada"""
        # Arrange
        account_repository.get_by_id = AsyncMock(side_effect=AccountNotFoundException(account_id=999))

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_repository.update_balance(account_id=999, new_balance=Decimal("1000.00"))

        account_repository.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_get_balance_success(self, account_repository, sample_account_data):
        """Testa busca de saldo com sucesso"""
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        # Act
        result = await account_repository.get_balance(account_id=1)

        # Assert
        assert result == Decimal("1000.00")
        account_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_balance_not_found(self, account_repository):
        """Testa busca de saldo para conta não encontrada"""
        # Arrange
        account_repository.get_by_id = AsyncMock(side_effect=AccountNotFoundException(account_id=999))

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_repository.get_balance(account_id=999)

        account_repository.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_account_exists_by_id_true(self, account_repository, sample_account_data):
        """Testa verificação de existência de conta por ID (existe)"""
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        # Act
        result = await account_repository.account_exists_by_id(account_id=1)

        # Assert
        assert result is True
        account_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_account_exists_by_id_false(self, account_repository):
        """Testa verificação de existência de conta por ID (não existe)"""
        # Arrange
        account_repository.get_by_id = AsyncMock(side_effect=AccountNotFoundException(account_id=999))

        # Act
        result = await account_repository.account_exists_by_id(account_id=999)

        # Assert
        assert result is False
        account_repository.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_account_exists_by_user_id_true(self, account_repository, sample_account_data):
        """Testa verificação de existência de conta por user_id (existe)"""
        # Arrange
        account_repository.get_by_user_id = AsyncMock(return_value=sample_account_data)

        # Act
        result = await account_repository.account_exists_by_user_id(user_id=123)

        # Assert
        assert result is True
        account_repository.get_by_user_id.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_account_exists_by_user_id_false(self, account_repository):
        """Testa verificação de existência de conta por user_id (não existe)"""
        # Arrange
        account_repository.get_by_user_id = AsyncMock(side_effect=AccountNotFoundException(user_id=999))

        # Act
        result = await account_repository.account_exists_by_user_id(user_id=999)

        # Assert
        assert result is False
        account_repository.get_by_user_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_create_with_different_balance(self, account_repository, mock_db, sample_account_create):
        """Testa criação de conta com saldo diferente"""
        # Arrange
        account_repository.get_by_user_id = AsyncMock(side_effect=AccountNotFoundException(user_id=123))

        account_data = AccountCreate(user_id=123, balance=Decimal("500.50"))

        expected_result = {
            "id": 2,
            "user_id": 123,
            "balance": Decimal("500.50"),
            "created_at": "2023-01-01T00:00:00"
        }

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=expected_result)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.create(account_data=account_data)

        # Assert
        assert result == expected_result
        assert result["balance"] == Decimal("500.50")
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_partial_data(self, account_repository, mock_db, sample_account_data):
        """Testa atualização com dados parciais"""
        # Arrange
        account_repository.get_by_id = AsyncMock(return_value=sample_account_data)

        partial_update = AccountUpdate(balance=Decimal("750.25"))

        updated_data = {**sample_account_data, "balance": Decimal("750.25")}

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_mapping=updated_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_repository.update(account_id=1, account_data=partial_update)

        # Assert
        assert result["balance"] == Decimal("750.25")
        account_repository.get_by_id.assert_called_once_with(1)
        mock_db.execute.assert_called_once()