import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from account.src.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from account.src.service.account_service import AccountService
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
    DuplicateAccountException,
    InvalidAmountException
)


class TestAccountService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def account_service(self, mock_db):
        return AccountService(mock_db)

    @pytest.fixture
    def sample_account_data(self):
        return {
            "id": 1,
            "user_id": 123,
            "balance": Decimal("1000.00"),
            "created_at": "2023-01-01T00:00:00"
        }

    @pytest.fixture
    def sample_account_response(self, sample_account_data):
        return AccountResponse(**sample_account_data)

    @pytest.mark.asyncio
    async def test_get_all_accounts_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_account_records = [sample_account_data]

        with patch.object(account_service.repository, 'get_all', return_value=mock_account_records) as mock_get_all:
            # Act
            result = await account_service.get_all_accounts(skip=0, limit=100)

            # Assert
            assert len(result) == 1
            assert result[0].id == sample_account_data["id"]
            assert result[0].user_id == sample_account_data["user_id"]
            assert result[0].balance == sample_account_data["balance"]
            mock_get_all.assert_called_once_with(0, 100)

    @pytest.mark.asyncio
    async def test_get_all_accounts_empty(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_all', return_value=[]) as mock_get_all:
            # Act
            result = await account_service.get_all_accounts()

            # Assert
            assert len(result) == 0
            mock_get_all.assert_called_once_with(0, 100)

    @pytest.mark.asyncio
    async def test_get_account_by_id_success(self, account_service, sample_account_data):
        # Arrange
        with patch.object(account_service.repository, 'get_by_id', return_value=sample_account_data) as mock_get:
            # Act
            result = await account_service.get_account_by_id(1)

            # Assert
            assert result.id == sample_account_data["id"]
            assert result.user_id == sample_account_data["user_id"]
            mock_get.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_by_id', side_effect=AccountNotFoundException(1)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.get_account_by_id(999)

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_success(self, account_service, sample_account_data):
        # Arrange
        with patch.object(account_service.repository, 'get_by_user_id', return_value=sample_account_data) as mock_get:
            # Act
            result = await account_service.get_account_by_user_id(123)

            # Assert
            assert result.user_id == sample_account_data["user_id"]
            mock_get.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_not_found(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_by_user_id', side_effect=AccountNotFoundException(999)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.get_account_by_user_id(999)

    @pytest.mark.asyncio
    async def test_create_account_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        with patch.object(account_service.repository, 'create', return_value=sample_account_data) as mock_create:
            # Act
            result = await account_service.create_account(account_data)

            # Assert
            assert result.id == sample_account_data["id"]
            assert result.user_id == account_data.user_id
            mock_create.assert_called_once_with(account_data)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_account_duplicate(self, account_service):
        # Arrange
        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        with patch.object(account_service.repository, 'create', side_effect=DuplicateAccountException(123)):
            # Act & Assert
            with pytest.raises(DuplicateAccountException):
                await account_service.create_account(account_data)

    @pytest.mark.asyncio
    async def test_create_account_rollback_on_error(self, account_service, mock_db):
        # Arrange
        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        with patch.object(account_service.repository, 'create', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.create_account(account_data)

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_account_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("1500.00")
        account_data = AccountUpdate(balance=Decimal("1500.00"))

        with patch.object(account_service.repository, 'update', return_value=updated_data) as mock_update:
            # Act
            result = await account_service.update_account(1, account_data)

            # Assert
            assert result.balance == Decimal("1500.00")
            mock_update.assert_called_once_with(1, account_data)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_account_no_changes(self, account_service, mock_db, sample_account_data):
        # Arrange
        account_data = AccountUpdate()

        with patch.object(account_service.repository, 'update', return_value=sample_account_data) as mock_update:
            # Act
            result = await account_service.update_account(1, account_data)

            # Assert
            assert result.balance == sample_account_data["balance"]
            mock_update.assert_called_once_with(1, account_data)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_account_not_found(self, account_service):
        # Arrange
        account_data = AccountUpdate(balance=Decimal("1500.00"))

        with patch.object(account_service.repository, 'update', side_effect=AccountNotFoundException(999)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.update_account(999, account_data)

    @pytest.mark.asyncio
    async def test_update_account_rollback_on_error(self, account_service, mock_db):
        # Arrange
        account_data = AccountUpdate(balance=Decimal("1500.00"))

        with patch.object(account_service.repository, 'update', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.update_account(1, account_data)

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_account_success(self, account_service, mock_db):
        # Arrange
        with patch.object(account_service.repository, 'delete', return_value=True) as mock_delete:
            # Act
            result = await account_service.delete_account(1)

            # Assert
            assert result is True
            mock_delete.assert_called_once_with(1)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_account_not_found(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'delete', side_effect=AccountNotFoundException(999)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.delete_account(999)

    @pytest.mark.asyncio
    async def test_delete_account_rollback_on_error(self, account_service, mock_db):
        # Arrange
        with patch.object(account_service.repository, 'delete', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.delete_account(1)

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_deposit_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("1500.00")

        with patch.object(account_service.repository, 'get_balance',
                          return_value=Decimal("1000.00")) as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance',
                             return_value=updated_data) as mock_update_balance:
            # Act
            result = await account_service.deposit(1, Decimal("500.00"))

            # Assert
            assert result.balance == Decimal("1500.00")
            mock_get_balance.assert_called_once_with(1)
            mock_update_balance.assert_called_once_with(1, Decimal("1500.00"))
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deposit_success_with_zero_initial_balance(self, account_service, mock_db):
        # Arrange
        account_data = {
            "id": 1,
            "user_id": 123,
            "balance": Decimal("500.00"),
            "created_at": "2023-01-01T00:00:00"
        }

        with patch.object(account_service.repository, 'get_balance', return_value=Decimal("0.00")) as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance',
                             return_value=account_data) as mock_update_balance:
            # Act
            result = await account_service.deposit(1, Decimal("500.00"))

            # Assert
            assert result.balance == Decimal("500.00")
            mock_get_balance.assert_called_once_with(1)
            mock_update_balance.assert_called_once_with(1, Decimal("500.00"))
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount_zero(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.deposit(1, Decimal("0.00"))

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount_negative(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.deposit(1, Decimal("-100.00"))

    @pytest.mark.asyncio
    async def test_deposit_account_not_found(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_balance', side_effect=AccountNotFoundException(999)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.deposit(999, Decimal("100.00"))

    @pytest.mark.asyncio
    async def test_deposit_rollback_on_error(self, account_service, mock_db):
        # Arrange
        with patch.object(account_service.repository, 'get_balance', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.deposit(1, Decimal("100.00"))

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("500.00")

        with patch.object(account_service.repository, 'get_balance',
                          return_value=Decimal("1000.00")) as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance',
                             return_value=updated_data) as mock_update_balance:
            # Act
            result = await account_service.withdraw(1, Decimal("500.00"))

            # Assert
            assert result.balance == Decimal("500.00")
            mock_get_balance.assert_called_once_with(1)
            mock_update_balance.assert_called_once_with(1, Decimal("500.00"))
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_exact_balance(self, account_service, mock_db, sample_account_data):
        # Arrange
        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("0.00")

        with patch.object(account_service.repository, 'get_balance',
                          return_value=Decimal("1000.00")) as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance',
                             return_value=updated_data) as mock_update_balance:
            # Act
            result = await account_service.withdraw(1, Decimal("1000.00"))

            # Assert
            assert result.balance == Decimal("0.00")
            mock_get_balance.assert_called_once_with(1)
            mock_update_balance.assert_called_once_with(1, Decimal("0.00"))
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_balance(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_balance', return_value=Decimal("1000.00")):
            # Act & Assert
            with pytest.raises(InsufficientBalanceException):
                await account_service.withdraw(1, Decimal("2000.00"))

    @pytest.mark.asyncio
    async def test_withdraw_invalid_amount_zero(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.withdraw(1, Decimal("0.00"))

    @pytest.mark.asyncio
    async def test_withdraw_invalid_amount_negative(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.withdraw(1, Decimal("-100.00"))

    @pytest.mark.asyncio
    async def test_withdraw_account_not_found(self, account_service):
        # Arrange
        with patch.object(account_service.repository, 'get_balance', side_effect=AccountNotFoundException(999)):
            # Act & Assert
            with pytest.raises(AccountNotFoundException):
                await account_service.withdraw(999, Decimal("100.00"))

    @pytest.mark.asyncio
    async def test_withdraw_rollback_on_error(self, account_service, mock_db):
        # Arrange
        with patch.object(account_service.repository, 'get_balance', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.withdraw(1, Decimal("100.00"))

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_transfer_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        from_account_data = sample_account_data.copy()
        from_account_data["id"] = 1
        from_account_data["balance"] = Decimal("500.00")

        to_account_data = sample_account_data.copy()
        to_account_data["id"] = 2
        to_account_data["balance"] = Decimal("1000.00")

        with patch.object(account_service.repository, 'get_by_id') as mock_get_by_id, \
                patch.object(account_service.repository, 'get_balance') as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance') as mock_update_balance:
            mock_get_by_id.side_effect = [from_account_data, to_account_data]
            mock_get_balance.side_effect = [Decimal("1000.00"), Decimal("500.00")]
            mock_update_balance.side_effect = [from_account_data, to_account_data]

            # Act
            result = await account_service.transfer(1, 2, Decimal("500.00"))

            # Assert
            assert result["from_account"].balance == Decimal("500.00")
            assert result["to_account"].balance == Decimal("1000.00")
            assert result["amount"] == Decimal("500.00")
            assert result["message"] == "Transfer completed successfully"
            assert mock_get_by_id.call_count == 2
            assert mock_get_balance.call_count == 2
            assert mock_update_balance.call_count == 2

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(self, account_service):
        # Arrange
        from_account_data = {"id": 1, "user_id": 123, "balance": Decimal("100.00"), "created_at": "2023-01-01T00:00:00"}
        to_account_data = {"id": 2, "user_id": 124, "balance": Decimal("500.00"), "created_at": "2023-01-01T00:00:00"}

        with patch.object(account_service.repository, 'get_by_id') as mock_get_by_id, \
                patch.object(account_service.repository, 'get_balance') as mock_get_balance:
            mock_get_by_id.side_effect = [from_account_data, to_account_data]
            mock_get_balance.side_effect = [Decimal("100.00"), Decimal("500.00")]

            # Act & Assert
            with pytest.raises(InsufficientBalanceException):
                await account_service.transfer(1, 2, Decimal("500.00"))

    @pytest.mark.asyncio
    async def test_transfer_invalid_amount_zero(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.transfer(1, 2, Decimal("0.00"))

    @pytest.mark.asyncio
    async def test_transfer_invalid_amount_negative(self, account_service):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.transfer(1, 2, Decimal("-100.00"))

    @pytest.mark.asyncio
    async def test_transfer_rollback_on_error(self, account_service, mock_db):
        # Arrange
        with patch.object(account_service.repository, 'get_by_id', side_effect=Exception("Database error")):
            # Act & Assert
            with pytest.raises(Exception):
                await account_service.transfer(1, 2, Decimal("100.00"))

            # Assert rollback was called
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_transfer_same_account(self, account_service, mock_db, sample_account_data):
        # Arrange
        from_account_data = sample_account_data.copy()
        from_account_data["id"] = 1
        from_account_data["balance"] = Decimal("500.00")

        with patch.object(account_service.repository, 'get_by_id', return_value=from_account_data) as mock_get_by_id, \
                patch.object(account_service.repository, 'get_balance',
                             return_value=Decimal("1000.00")) as mock_get_balance, \
                patch.object(account_service.repository, 'update_balance',
                             return_value=from_account_data) as mock_update_balance:
            # Act
            result = await account_service.transfer(1, 1, Decimal("500.00"))

            # Assert
            assert result["from_account"].balance == Decimal("500.00")
            assert result["to_account"].balance == Decimal("500.00")
            assert result["amount"] == Decimal("500.00")
            # Should call get_by_id twice (for from_account and to_account, even if same)
            assert mock_get_by_id.call_count == 2
            assert mock_get_balance.call_count == 2
            assert mock_update_balance.call_count == 2

    @pytest.mark.asyncio
    async def test_create_and_retrieve_account(self, account_service, mock_db):
        # Arrange
        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))
        created_account_data = {
            "id": 1,
            "user_id": 123,
            "balance": Decimal("1000.00"),
            "created_at": "2023-01-01T00:00:00"
        }

        with patch.object(account_service.repository, 'create', return_value=created_account_data) as mock_create, \
                patch.object(account_service.repository, 'get_by_id',
                             return_value=created_account_data) as mock_get_by_id:
            # Act - Create
            created_account = await account_service.create_account(account_data)

            # Act - Retrieve
            retrieved_account = await account_service.get_account_by_id(1)

            # Assert
            assert created_account.id == 1
            assert retrieved_account.id == 1
            assert created_account.user_id == retrieved_account.user_id
            assert created_account.balance == retrieved_account.balance
            mock_create.assert_called_once_with(account_data)
            mock_get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_db):
        # Act
        service = AccountService(mock_db)

        # Assert
        assert service.db == mock_db
        assert service.repository is not None

    @pytest.mark.asyncio
    async def test_get_all_accounts_with_pagination(self, account_service, sample_account_data):
        # Arrange
        mock_account_records = [
            sample_account_data,
            {**sample_account_data, "id": 2, "user_id": 124}
        ]

        with patch.object(account_service.repository, 'get_all', return_value=mock_account_records) as mock_get_all:
            # Act
            result = await account_service.get_all_accounts(skip=5, limit=10)

            # Assert
            assert len(result) == 2
            assert result[0].id == 1
            assert result[1].id == 2
            mock_get_all.assert_called_once_with(5, 10)