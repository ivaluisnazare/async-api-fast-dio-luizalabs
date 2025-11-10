import pytest
from unittest.mock import AsyncMock, patch

from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    DuplicateAccountException,
    InvalidAmountException
)


class TestAccountController:

    @pytest.mark.asyncio
    async def test_get_all_accounts_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_all_accounts',
                  new_callable=AsyncMock,
                  side_effect=Exception("Internal server error")):
            # Act
            response = await async_client.get("/accounts/")

        # Assert
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_account_by_id_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_account_by_id',
                  new_callable=AsyncMock,
                  side_effect=Exception("Database error")):
            # Act
            response = await async_client.get("/accounts/1")

        # Assert
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_account_by_user_id',
                  new_callable=AsyncMock,
                  side_effect=Exception("Database error")):
            # Act
            response = await async_client.get("/accounts/user/1")

        # Assert
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_account_internal_error(self, async_client):
        # Arrange
        account_data = {
            "user_id": 1,
            "balance": "100.00"
        }

        with patch('account.src.service.account_service.AccountService.create_account',
                  new_callable=AsyncMock,
                  side_effect=Exception("Creation failed")):
            # Act
            response = await async_client.post("/accounts/", json=account_data)

        # Assert
        assert response.status_code == 500
        assert "Creation failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_account_internal_error(self, async_client):
        # Arrange
        update_data = {
            "balance": "200.00"
        }

        with patch('account.src.service.account_service.AccountService.update_account',
                  new_callable=AsyncMock,
                  side_effect=Exception("Update failed")):
            # Act
            response = await async_client.put("/accounts/1", json=update_data)

        # Assert
        assert response.status_code == 500
        assert "Update failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_account_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.delete_account',
                  new_callable=AsyncMock,
                  side_effect=Exception("Deletion failed")):
            # Act
            response = await async_client.delete("/accounts/1")

        # Assert
        assert response.status_code == 500
        assert "Deletion failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_deposit_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.deposit',
                  new_callable=AsyncMock,
                  side_effect=Exception("Deposit failed")):
            # Act
            response = await async_client.post("/accounts/1/deposit?amount=50.00")

        # Assert
        assert response.status_code == 500
        assert "Deposit failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_withdraw_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.withdraw',
                  new_callable=AsyncMock,
                  side_effect=Exception("Withdrawal failed")):
            # Act
            response = await async_client.post("/accounts/1/withdraw?amount=50.00")

        # Assert
        assert response.status_code == 500
        assert "Withdrawal failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_transfer_internal_error(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.transfer',
                  new_callable=AsyncMock,
                  side_effect=Exception("Transfer failed")):
            # Act
            response = await async_client.post("/accounts/1/transfer/2?amount=50.00")

        # Assert
        assert response.status_code == 500
        assert "Transfer failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_all_accounts_invalid_skip(self, async_client):
        # Act
        response = await async_client.get("/accounts/?skip=-1")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_all_accounts_invalid_limit_zero(self, async_client):
        # Act
        response = await async_client.get("/accounts/?limit=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_all_accounts_invalid_limit_exceeded(self, async_client):
        # Act
        response = await async_client.get("/accounts/?limit=1001")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_deposit_zero_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/deposit?amount=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_withdraw_zero_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/withdraw?amount=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transfer_zero_amount(self, async_client):
        # Act
        response = await async_client.post("/accounts/1/transfer/2?amount=0")

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_account_not_found_error_format(self, async_client):
        # Arrange
        with patch('account.src.service.account_service.AccountService.get_account_by_id',
                  new_callable=AsyncMock,
                  side_effect=AccountNotFoundException(account_id=999)):
            # Act
            response = await async_client.get("/accounts/999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "" in data["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_account_error_format(self, async_client):
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
        data = response.json()
        assert "detail" in data
        assert "" in data["detail"]