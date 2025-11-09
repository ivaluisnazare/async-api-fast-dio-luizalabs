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
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(_asdict=lambda: sample_account_data)
        ]
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_service.get_all_accounts(skip=0, limit=100)

        # Assert
        assert len(result) == 1
        assert result[0].id == sample_account_data["id"]
        assert result[0].user_id == sample_account_data["user_id"]
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_accounts_empty(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_service.get_all_accounts()

        # Assert
        assert len(result) == 0
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account_by_id_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_service.get_account_by_id(1)

        # Assert
        assert result.id == sample_account_data["id"]
        assert result.user_id == sample_account_data["user_id"]
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.get_account_by_id(999)

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_service.get_account_by_user_id(123)

        # Assert
        assert result.user_id == sample_account_data["user_id"]
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.get_account_by_user_id(999)

    @pytest.mark.asyncio
    async def test_create_account_success(self, account_service, mock_db, sample_account_data):
        mock_result_existing = MagicMock()
        mock_result_existing.fetchone.return_value = None

        mock_result_insert = MagicMock()
        mock_result_insert.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)

        mock_db.execute.side_effect = [mock_result_existing, mock_result_insert]

        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        # Act
        result = await account_service.create_account(account_data)

        # Assert
        assert result.id == sample_account_data["id"]
        assert result.user_id == account_data.user_id
        assert mock_db.commit.called
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_create_account_duplicate(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: {"user_id": 123})
        mock_db.execute.return_value = mock_result

        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        # Act & Assert
        with pytest.raises(DuplicateAccountException):
            await account_service.create_account(account_data)

    @pytest.mark.asyncio
    async def test_update_account_success(self, account_service, mock_db, sample_account_data):
        mock_result_get = MagicMock()
        mock_result_get.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)

        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("1500.00")
        mock_result_update = MagicMock()
        mock_result_update.fetchone.return_value = MagicMock(_asdict=lambda: updated_data)

        mock_db.execute.side_effect = [mock_result_get, mock_result_update]

        account_data = AccountUpdate(balance=Decimal("1500.00"))

        # Act
        result = await account_service.update_account(1, account_data)

        # Assert
        assert result.balance == Decimal("1500.00")
        assert mock_db.commit.called
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def  test_update_account_no_changes(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)
        mock_db.execute.return_value = mock_result

        account_data = AccountUpdate()

        # Act
        result = await account_service.update_account(1, account_data)

        # Assert
        assert result.balance == sample_account_data["balance"]
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_account_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        account_data = AccountUpdate(balance=Decimal("1500.00"))

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.update_account(999, account_data)

    @pytest.mark.asyncio
    async def test_delete_account_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_result_get = MagicMock()
        mock_result_get.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)
        mock_db.execute.return_value = mock_result_get

        # Act
        result = await account_service.delete_account(1)

        # Assert
        assert result is True
        assert mock_db.commit.called
        assert mock_db.execute.call_count == 2  # get + delete

    @pytest.mark.asyncio
    async def test_delete_account_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.delete_account(999)

    @pytest.mark.asyncio
    async def test_deposit_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("1500.00")

        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: updated_data)
        mock_db.execute.return_value = mock_result

        # Act
        result = await account_service.deposit(1, Decimal("500.00"))

        # Assert
        assert result.balance == Decimal("1500.00")
        assert mock_db.commit.called
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount(self, account_service, mock_db):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.deposit(1, Decimal("0.00"))

        with pytest.raises(InvalidAmountException):
            await account_service.deposit(1, Decimal("-100.00"))

    @pytest.mark.asyncio
    async def test_deposit_account_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.deposit(999, Decimal("100.00"))

    @pytest.mark.asyncio
    async def test_withdraw_success(self, account_service, mock_db, sample_account_data):
        mock_result_get = MagicMock()
        mock_result_get.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)

        updated_data = sample_account_data.copy()
        updated_data["balance"] = Decimal("500.00")
        mock_result_update = MagicMock()
        mock_result_update.fetchone.return_value = MagicMock(_asdict=lambda: updated_data)

        mock_db.execute.side_effect = [mock_result_get, mock_result_update]

        # Act
        result = await account_service.withdraw(1, Decimal("500.00"))

        # Assert
        assert result.balance == Decimal("500.00")
        assert mock_db.commit.called
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_balance(self, account_service, mock_db, sample_account_data):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(_asdict=lambda: sample_account_data)
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(InsufficientBalanceException):
            await account_service.withdraw(1, Decimal("2000.00"))

    @pytest.mark.asyncio
    async def test_withdraw_invalid_amount(self, account_service, mock_db):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.withdraw(1, Decimal("0.00"))

    @pytest.mark.asyncio
    async def test_withdraw_account_not_found(self, account_service, mock_db):
        # Arrange
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            await account_service.withdraw(999, Decimal("100.00"))

    @pytest.mark.asyncio
    async def test_transfer_success(self, account_service, mock_db, sample_account_data):
        # Arrange
        from_account_data = sample_account_data.copy()
        from_account_data["id"] = 1
        from_account_data["balance"] = Decimal("1000.00")

        to_account_data = sample_account_data.copy()
        to_account_data["id"] = 2
        to_account_data["balance"] = Decimal("500.00")

        mock_result_get1 = MagicMock()
        mock_result_get1.fetchone.return_value = MagicMock(_asdict=lambda: from_account_data)

        mock_result_get2 = MagicMock()
        mock_result_get2.fetchone.return_value = MagicMock(_asdict=lambda: to_account_data)

        from_updated = from_account_data.copy()
        from_updated["balance"] = Decimal("500.00")
        mock_result_withdraw = MagicMock()
        mock_result_withdraw.fetchone.return_value = MagicMock(_asdict=lambda: from_updated)

        to_updated = to_account_data.copy()
        to_updated["balance"] = Decimal("1000.00")
        mock_result_deposit = MagicMock()
        mock_result_deposit.fetchone.return_value = MagicMock(_asdict=lambda: to_updated)

        mock_db.execute.side_effect = [
            mock_result_get1,  # get from_account
            mock_result_get2,  # get to_account
            mock_result_get1,  # get_account_by_id no withdraw
            mock_result_withdraw,  # update no withdraw
            mock_result_deposit  # update no deposit
        ]

        # Act
        result = await account_service.transfer(1, 2, Decimal("500.00"))

        # Assert
        assert result["from_account"].balance == Decimal("500.00")
        assert result["to_account"].balance == Decimal("1000.00")
        assert result["amount"] == Decimal("500.00")
        assert result["message"] == "Transfer completed successfully"

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(self, account_service, mock_db, sample_account_data):
        # Arrange
        from_account_data = sample_account_data.copy()
        from_account_data["id"] = 1
        from_account_data["balance"] = Decimal("100.00")

        to_account_data = sample_account_data.copy()
        to_account_data["id"] = 2
        to_account_data["balance"] = Decimal("500.00")

        mock_result_get1 = MagicMock()
        mock_result_get1.fetchone.return_value = MagicMock(_asdict=lambda: from_account_data)

        mock_result_get2 = MagicMock()
        mock_result_get2.fetchone.return_value = MagicMock(_asdict=lambda: to_account_data)

        mock_db.execute.side_effect = [mock_result_get1,
                                       mock_result_get2,
                                       mock_result_get1
                                       ]

        # Act & Assert
        with pytest.raises(InsufficientBalanceException):
            await account_service.transfer(1, 2, Decimal("500.00"))

    @pytest.mark.asyncio
    async def test_transfer_invalid_amount(self, account_service, mock_db):
        # Act & Assert
        with pytest.raises(InvalidAmountException):
            await account_service.transfer(1, 2, Decimal("0.00"))

    @pytest.mark.asyncio
    async def test_transfer_rollback_on_error(self, account_service, mock_db, sample_account_data):
        # Arrange
        from_account_data = sample_account_data.copy()
        from_account_data["id"] = 1

        to_account_data = sample_account_data.copy()
        to_account_data["id"] = 2

        mock_result_get1 = MagicMock()
        mock_result_get1.fetchone.return_value = MagicMock(_asdict=lambda: from_account_data)

        mock_result_get2 = MagicMock()
        mock_result_get2.fetchone.return_value = MagicMock(_asdict=lambda: to_account_data)

        # Simula um erro durante o withdraw
        mock_db.execute.side_effect = [
            mock_result_get1,
            mock_result_get2,
            Exception("Database error")
        ]

        # Act & Assert
        with pytest.raises(Exception):
            await account_service.transfer(1, 2, Decimal("100.00"))

        assert mock_db.rollback.called

    @pytest.mark.asyncio
    async def test_create_and_retrieve_account(self, account_service, mock_db):
        # Arrange - Create
        account_data = AccountCreate(user_id=123, balance=Decimal("1000.00"))

        mock_result_existing = MagicMock()
        mock_result_existing.fetchone.return_value = None

        created_account_data = {
            "id": 1,
            "user_id": 123,
            "balance": Decimal("1000.00"),
            "created_at": "2023-01-01T00:00:00"
        }
        mock_result_create = MagicMock()
        mock_result_create.fetchone.return_value = MagicMock(_asdict=lambda: created_account_data)

        # Arrange - Retrieve
        mock_result_retrieve = MagicMock()
        mock_result_retrieve.fetchone.return_value = MagicMock(_asdict=lambda: created_account_data)

        mock_db.execute.side_effect = [
            mock_result_existing,  # Check existing
            mock_result_create,  # Create account
            mock_result_retrieve  # Retrieve account
        ]

        # Act - Create
        created_account = await account_service.create_account(account_data)

        # Act - Retrieve
        retrieved_account = await account_service.get_account_by_id(1)

        # Assert
        assert created_account.id == 1
        assert retrieved_account.id == 1
        assert created_account.user_id == retrieved_account.user_id
        assert created_account.balance == retrieved_account.balance