from datetime import datetime
from decimal import Decimal

import pytest
from account.src.schemas.account import (AccountBalanceResponse, AccountBase,
                                         AccountCreate, AccountResponse,
                                         AccountUpdate)
from pydantic import ValidationError


class TestAccountBase:
    def test_account_base_valid_data(self):
        data = {"user_id": 1, "balance": Decimal("100.50")}

        account = AccountBase(**data)

        assert account.user_id == 1
        assert account.balance == Decimal("100.50")

    def test_account_base_default_balance(self):
        data = {"user_id": 1}

        account = AccountBase(**data)

        assert account.user_id == 1
        assert account.balance == Decimal("0")

    def test_account_base_negative_balance_raises_error(self):
        data = {"user_id": 1, "balance": Decimal("-10.00")}

        with pytest.raises(ValidationError) as exc_info:
            AccountBase(**data)

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_account_base_balance_decimal_places(self):
        data = {"user_id": 1, "balance": Decimal("100.123")}

        with pytest.raises(ValidationError):
            AccountBase(**data)

    def test_account_base_missing_user_id_raises_error(self):
        data = {"balance": Decimal("100.00")}

        with pytest.raises(ValidationError) as exc_info:
            AccountBase(**data)

        assert "user_id" in str(exc_info.value)


class TestAccountCreate:

    def test_account_create_inherits_account_base(self):
        data = {"user_id": 1, "balance": Decimal("50.00")}

        account_create = AccountCreate(**data)

        assert account_create.user_id == 1
        assert account_create.balance == Decimal("50.00")
        assert isinstance(account_create, AccountBase)


class TestAccountUpdate:

    def test_account_update_with_balance(self):
        data = {"balance": Decimal("200.00")}

        account_update = AccountUpdate(**data)

        assert account_update.balance == Decimal("200.00")

    def test_account_update_with_none_balance(self):
        data = {"balance": None}

        account_update = AccountUpdate(**data)

        assert account_update.balance is None

    def test_account_update_empty_data(self):
        account_update = AccountUpdate()

        assert account_update.balance is None

    def test_account_update_negative_balance_raises_error(self):
        data = {"balance": Decimal("-50.00")}

        with pytest.raises(ValidationError):
            AccountUpdate(**data)


class TestAccountResponse:

    def test_account_response_valid_data(self):
        data = {
            "id": 1,
            "user_id": 1,
            "balance": Decimal("150.75"),
            "created_at": datetime.now(),
        }

        account_response = AccountResponse(**data)

        assert account_response.id == 1
        assert account_response.user_id == 1
        assert account_response.balance == Decimal("150.75")
        assert isinstance(account_response.created_at, datetime)

    def test_account_response_from_attributes_config(self):

        class MockORMObject:
            def __init__(self):
                self.id = 1
                self.user_id = 1
                self.balance = Decimal("100.00")
                self.created_at = datetime.now()

        mock_obj = MockORMObject()

        account_response = AccountResponse.model_validate(mock_obj)

        assert account_response.id == 1
        assert account_response.user_id == 1
        assert account_response.balance == Decimal("100.00")
        assert isinstance(account_response.created_at, datetime)


class TestAccountBalanceResponse:

    def test_account_balance_response_valid_data(self):
        data = {
            "account_id": 1,
            "user_id": 1,
            "balance": Decimal("300.25"),
            "updated_at": datetime.now(),
        }

        balance_response = AccountBalanceResponse(**data)

        assert balance_response.account_id == 1
        assert balance_response.user_id == 1
        assert balance_response.balance == Decimal("300.25")
        assert isinstance(balance_response.updated_at, datetime)

    def test_account_balance_response_missing_fields_raise_error(self):
        data = {
            "user_id": 1,
            "balance": Decimal("100.00"),
            "updated_at": datetime.now(),
        }

        with pytest.raises(ValidationError):
            AccountBalanceResponse(**data)

        data = {
            "account_id": 1,
            "balance": Decimal("100.00"),
            "updated_at": datetime.now(),
        }

        with pytest.raises(ValidationError):
            AccountBalanceResponse(**data)


class TestAccountEdgeCases:

    def test_account_base_zero_balance(self):
        """Testa balance zero"""
        data = {"user_id": 1, "balance": Decimal("0.00")}

        account = AccountBase(**data)
        assert account.balance == Decimal("0.00")

    def test_account_base_large_balance(self):
        data = {
            "user_id": 1,
            "balance": Decimal("9999999.99"),  # max_digits=10, decimal_places=2
        }

        account = AccountBase(**data)
        assert account.balance == Decimal("9999999.99")

    def test_account_base_balance_exceeds_max_digits(self):
        data = {"user_id": 1, "balance": Decimal("100000000.00")}

        with pytest.raises(ValidationError):
            AccountBase(**data)

    def test_account_response_datetime_parsing(self):
        from datetime import datetime

        data = {
            "id": 1,
            "user_id": 1,
            "balance": Decimal("100.00"),
            "created_at": "2023-10-01T12:00:00",
        }

        account_response = AccountResponse(**data)
        assert isinstance(account_response.created_at, datetime)
        assert account_response.created_at.year == 2023
        assert account_response.created_at.month == 10
