import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status


class MockAccountResponse:

    def __init__(self, id=1, user_id=1, balance=Decimal("1000.00"), created_at="2024-01-01T00:00:00"):
        self.id = id
        self.user_id = user_id
        self.balance = balance
        self.created_at = created_at

    def model_dump(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": str(self.balance),
            "created_at": self.created_at
        }


class TestAccountController:

    @pytest.mark.asyncio
    async def test_get_all_accounts_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_accounts = [
                MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00")),
                MockAccountResponse(id=2, user_id=2, balance=Decimal("2000.00"))
            ]

            mock_service_instance = AsyncMock()
            mock_service_instance.get_all_accounts.return_value = mock_accounts
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/", params={"skip": 0, "limit": 10})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_get_all_accounts_with_pagination(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_accounts = [
                MockAccountResponse(id=3, user_id=3, balance=Decimal("3000.00"))
            ]

            mock_service_instance = AsyncMock()
            mock_service_instance.get_all_accounts.return_value = mock_accounts
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/", params={"skip": 2, "limit": 1})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 3

    @pytest.mark.asyncio
    async def test_get_all_accounts_server_error(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_all_accounts.side_effect = Exception("Database error")
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Database error" in response.json()["detail"]

    # Testes para GET /accounts/{account_id}
    @pytest.mark.asyncio
    async def test_get_account_by_id_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_account
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/1")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == 1
            assert data["balance"] == "1000.00"

    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            from account.src.exceptions.custom_exceptions import AccountNotFoundException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.side_effect = AccountNotFoundException(account_id=999)
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_account_by_id_forbidden(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_account = MockAccountResponse(id=1, user_id=2, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_account
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/1")

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Not authorized" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_user_id.return_value = mock_account
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/user/1")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_id"] == 1

    @pytest.mark.asyncio
    async def test_get_account_by_user_id_not_found(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            from account.src.exceptions.custom_exceptions import AccountNotFoundException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_user_id.side_effect = AccountNotFoundException(user_id=999)
            mock_service.return_value = mock_service_instance

            response = await client.get("/accounts/user/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_account_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("0.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.create_account.return_value = mock_account
            mock_service.return_value = mock_service_instance

            account_data = {
                "user_id": 1,
                "balance": "0.00"
            }

            response = await client.post("/accounts/", json=account_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == 1

    @pytest.mark.asyncio
    async def test_create_account_duplicate(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            from account.src.exceptions.custom_exceptions import DuplicateAccountException

            mock_service_instance = AsyncMock()
            mock_service_instance.create_account.side_effect = DuplicateAccountException(user_id=1)
            mock_service.return_value = mock_service_instance

            account_data = {
                "user_id": 1,
                "balance": "0.00"
            }

            response = await client.post("/accounts/", json=account_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_update_account_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))
            mock_updated_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1500.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.update_account.return_value = mock_updated_account
            mock_service.return_value = mock_service_instance

            update_data = {"balance": "1500.00"}

            response = await client.put("/accounts/1", json=update_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["balance"] == "1500.00"

    @pytest.mark.asyncio
    async def test_update_account_not_found(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            from account.src.exceptions.custom_exceptions import AccountNotFoundException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.side_effect = AccountNotFoundException(account_id=999)
            mock_service.return_value = mock_service_instance

            update_data = {"balance": "1500.00"}

            response = await client.put("/accounts/999", json=update_data)

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_account_forbidden(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=2, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service.return_value = mock_service_instance

            update_data = {"balance": "1500.00"}

            response = await client.put("/accounts/1", json=update_data)

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_account_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.delete_account.return_value = True
            mock_service.return_value = mock_service_instance

            response = await client.delete("/accounts/1")

            assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_account_not_found(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            from account.src.exceptions.custom_exceptions import AccountNotFoundException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.side_effect = AccountNotFoundException(account_id=999)
            mock_service.return_value = mock_service_instance

            response = await client.delete("/accounts/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_account_forbidden(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=2, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service.return_value = mock_service_instance

            response = await client.delete("/accounts/1")

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_deposit_to_account_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))
            mock_updated_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1500.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.deposit.return_value = mock_updated_account
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/deposit?amount=500")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["balance"] == "1500.00"

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount(self, client):
        response = await client.post("/accounts/1/deposit?amount=-100")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deposit_invalid_amount_service_error(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))

            from account.src.exceptions.custom_exceptions import InvalidAmountException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.deposit.side_effect = InvalidAmountException(amount=Decimal("0"))
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/deposit?amount=0")

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deposit_amount_zero_not_allowed(self, client):
        response = await client.post("/accounts/1/deposit?amount=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_withdraw_from_account_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))
            mock_updated_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("500.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.withdraw.return_value = mock_updated_account
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/withdraw?amount=500")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["balance"] == "500.00"

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_balance(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_existing_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("100.00"))

            from account.src.exceptions.custom_exceptions import InsufficientBalanceException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_existing_account
            mock_service_instance.withdraw.side_effect = InsufficientBalanceException(
                account_id=1,
                current_balance=Decimal("100.00"),
                required_balance=Decimal("500.00")
            )
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/withdraw?amount=500")

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_transfer_between_accounts_success(self, client):
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_from_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("1000.00"))

            mock_transfer_result = {
                "from_account": MockAccountResponse(id=1, user_id=1, balance=Decimal("500.00")),
                "to_account": MockAccountResponse(id=2, user_id=2, balance=Decimal("1500.00")),
                "amount": Decimal("500.00"),
                "message": "Transfer completed successfully"
            }

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_from_account
            mock_service_instance.transfer.return_value = mock_transfer_result
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/transfer/2?amount=500")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert float(data["amount"]) == 500.0
            assert data["from_account"]["balance"] == 500.00
            assert data["to_account"]["balance"] == 1500.00

    @pytest.mark.asyncio
    async def test_transfer_forbidden(self, client):
        """Teste de transferência não autorizada"""
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_from_account = MockAccountResponse(id=1, user_id=2, balance=Decimal("1000.00"))

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_from_account
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/transfer/2?amount=500")

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(self, client):
        """Teste de transferência com saldo insuficiente"""
        with patch('account.src.controller.account_controller.AccountService') as mock_service:
            mock_from_account = MockAccountResponse(id=1, user_id=1, balance=Decimal("100.00"))

            from account.src.exceptions.custom_exceptions import InsufficientBalanceException

            mock_service_instance = AsyncMock()
            mock_service_instance.get_account_by_id.return_value = mock_from_account
            mock_service_instance.transfer.side_effect = InsufficientBalanceException(
                account_id=1,
                current_balance=Decimal("100.00"),
                required_balance=Decimal("500.00")
            )
            mock_service.return_value = mock_service_instance

            response = await client.post("/accounts/1/transfer/2?amount=500")

            assert response.status_code == status.HTTP_400_BAD_REQUEST