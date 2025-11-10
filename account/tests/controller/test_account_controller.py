import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from account.src.schemas.account import AccountResponse, AccountCreate, AccountUpdate
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
    DuplicateAccountException,
    InvalidAmountException
)


class TestAccountController:
    """Testes de integração para o AccountController"""

    @pytest.mark.asyncio
    async def test_get_all_accounts_success(self, async_client):
        """Testa a obtenção de todas as contas com sucesso"""
        # Arrange
        mock_accounts = [
            AccountResponse(
                id=1,
                user_id=1,
                balance=Decimal("100.00"),
                created_at="2023-01-01T00:00:00"
            ),
            AccountResponse(
                id=2,
                user_id=2,
                balance=Decimal("200.00"),
                created_at="2023-01-01T00:00:00"
            )
        ]

        with patch('account.src.service.account_service.AccountService.get_all_accounts',
                  new_callable=AsyncMock, return_value=mock_accounts):
            # Act
            response = await async_client.get("/accounts/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["user_id"] == 1
        assert data[0]["balance"] == "100.00"
        assert data[1]["id"] == 2
        assert data[1]["user_id"] == 2
        assert data[1]["balance"] == "200.00"

    @pytest.mark.asyncio
    async def test_get_all_accounts_with_pagination(self, async_client):
        """Testa a obtenção de contas com paginação"""
        # Arrange
        mock_accounts = [
            AccountResponse(
                id=1,
                user_id=1,
                balance=Decimal("100.00"),
                created_at="2023-01-01T00:00:00"
            )
        ]

        with patch('account.src.service.account_service.AccountService.get_all_accounts',
                  new_callable=AsyncMock, return_value=mock_accounts):
            # Act
            response = await async_client.get("/accounts/?skip=0&limit=1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_account_by_id_success(self, async_client):
        """Testa a obtenção de conta por ID com sucesso"""
        # Arrange
        mock_account = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("100.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.get_account_by_id',
                  new_callable=AsyncMock, return_value=mock_account):
            # Act
            response = await async_client.get("/accounts/1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["balance"] == "100.00"

    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_account_by_id',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.get("/accounts/1")

        # Assert
        assert response.status_code == 404
        assert "" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_success(self, async_client):
        # Arrange
        mock_account = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("150.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.get_account_by_user_id',
                  new_callable=AsyncMock, return_value=mock_account):
            # Act
            response = await async_client.get("/accounts/user/1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["balance"] == "150.00"

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_account_by_user_id',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(user_id=1)):
            # Act
            response = await async_client.get("/accounts/user/1")

        # Assert
        assert response.status_code == 404
        assert "" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_account_success(self, async_client):
        # Arrange
        account_data = {
            "user_id": 1,
            "balance": "100.00"
        }

        mock_account_response = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("100.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.create_account',
                  new_callable=AsyncMock, return_value=mock_account_response):
            # Act
            response = await async_client.post("/accounts/", json=account_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["balance"] == "100.00"

    @pytest.mark.asyncio
    async def test_create_account_duplicate(self, async_client):
        # Arrange
        account_data = {
            "user_id": 1,
            "balance": "100.00"
        }

        with patch('account.src.service.account_service.AccountService.create_account',
                  new_callable=AsyncMock,
                  side_effect=DuplicateAccountException(user_id=1)):
            # Act
            response = await async_client.post("/accounts/", json=account_data)

        # Assert
        assert response.status_code == 400
        assert "" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_account_success(self, async_client):
        # Arrange
        update_data = {
            "balance": "200.00"
        }

        mock_account_response = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("200.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.update_account',
                  new_callable=AsyncMock, return_value=mock_account_response):
            # Act
            response = await async_client.put("/accounts/1", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["balance"] == "200.00"

    @pytest.mark.asyncio
    async def test_update_account_not_found(self, async_client):
        # Arrange
        update_data = {
            "balance": "200.00"
        }

        with patch('account.src.service.account_service.AccountService.update_account',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.put("/accounts/1", json=update_data)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_account_success(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.delete_account',
                  new_callable=AsyncMock, return_value=True):
            # Act
            response = await async_client.delete("/accounts/1")

        # Assert
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_account_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.delete_account',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.delete("/accounts/1")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deposit_success(self, async_client):
        # Arrange
        mock_account_response = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("150.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.deposit',
                  new_callable=AsyncMock, return_value=mock_account_response):
            # Act
            response = await async_client.post("/accounts/1/deposit?amount=50.00")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == "150.00"

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.deposit',
                  new_callable=AsyncMock,
                  side_effect=InvalidAmountException(amount=Decimal("0"))):
            # Act
            response = await async_client.post("/accounts/1/deposit?amount=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_deposit_account_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.deposit',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.post("/accounts/1/deposit?amount=50.00")

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_withdraw_success(self, async_client):
        # Arrange
        mock_account_response = AccountResponse(
            id=1,
            user_id=1,
            balance=Decimal("50.00"),
            created_at="2023-01-01T00:00:00"
        )

        with patch('account.src.service.account_service.AccountService.withdraw',
                  new_callable=AsyncMock, return_value=mock_account_response):
            # Act
            response = await async_client.post("/accounts/1/withdraw?amount=50.00")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == "50.00"

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_balance(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.withdraw',
                  new_callable=AsyncMock,
                  side_effect=InsufficientBalanceException(
                      account_id=1,
                      current_balance=Decimal("10.00"),
                      required_balance=Decimal("50.00")
                  )):
            # Act
            response = await async_client.post("/accounts/1/withdraw?amount=50.00")

        # Assert
        assert response.status_code == 400
        assert "" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_withdraw_account_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.withdraw',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.post("/accounts/1/withdraw?amount=50.00")

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transfer_success(self, async_client):
        # Arrange
        mock_response = {
            "from_account": AccountResponse(
                id=1,
                user_id=1,
                balance=Decimal("50.0"),
                created_at="2023-01-01T00:00:00"
            ),
            "to_account": AccountResponse(
                id=2,
                user_id=2,
                balance=Decimal("150.00"),
                created_at="2023-01-01T00:00:00"
            ),
            "amount": Decimal("50.0"),
            "message": "Transfer completed successfully"
        }

        with patch('account.src.service.account_service.AccountService.transfer',
                  new_callable=AsyncMock, return_value=mock_response):
            # Act
            response = await async_client.post("/accounts/1/transfer/2?amount=50.00")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50.0
        assert data["message"] == "Transfer completed successfully"
        assert data["from_account"]["balance"] == "50.0"
        assert data["to_account"]["balance"] == "150.00"

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.transfer',
                  new_callable=AsyncMock,
                  side_effect=InsufficientBalanceException(
                      account_id=1,
                      current_balance=Decimal("10.00"),
                      required_balance=Decimal("50.00")
                  )):
            # Act
            response = await async_client.post("/accounts/1/transfer/2?amount=50.00")

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transfer_account_not_found(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.transfer',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=1)):
            # Act
            response = await async_client.post("/accounts/1/transfer/2?amount=50.00")

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transfer_invalid_amount(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.transfer',
                  new_callable=AsyncMock,
                  side_effect=InvalidAmountException(amount=Decimal("0"))):
            # Act
            response = await async_client.post("/accounts/1/transfer/2?amount=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_query_parameters(self, async_client):
        # Act
        response = await async_client.get("/accounts/?skip=-1&limit=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_deposit_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/deposit?amount=-10.00")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_withdraw_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/withdraw?amount=-10.00")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_transfer_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/transfer/2?amount=-10.00")

        # Assert
        assert response.status_code == 422