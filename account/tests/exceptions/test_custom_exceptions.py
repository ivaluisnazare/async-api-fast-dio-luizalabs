import pytest
from fastapi import HTTPException, status

from account.src.exceptions.custom_exceptions import AccountNotFoundException, InsufficientBalanceException, \
    DuplicateAccountException, InvalidAmountException, AccountException


class TestAccountExceptions:

    def test_account_exception_inheritance(self):
        assert issubclass(AccountException, HTTPException)

    def test_all_specific_exceptions_inherit_from_account_exception(self):
        specific_exceptions = [
            AccountNotFoundException,
            InsufficientBalanceException,
            DuplicateAccountException,
            InvalidAmountException
        ]

        for exception_class in specific_exceptions:
            assert issubclass(exception_class, AccountException)


class TestAccountNotFoundException:

    def test_account_not_found_with_account_id(self):
        account_id = 123
        exception = AccountNotFoundException(account_id=account_id)

        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert exception.detail == f"Account with id {account_id} not found"

    def test_account_not_found_with_user_id(self):
        user_id = 456
        exception = AccountNotFoundException(user_id=user_id)

        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert exception.detail == f"Account for user {user_id} not found"

    def test_account_not_found_without_parameters(self):
        exception = AccountNotFoundException()

        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert exception.detail == "Account not found"

    def test_account_not_found_priority_account_id(self):
        account_id = 123
        user_id = 456
        exception = AccountNotFoundException(account_id=account_id, user_id=user_id)

        assert exception.detail == f"Account with id {account_id} not found"


class TestInsufficientBalanceException:

    def test_insufficient_balance_exception(self):
        account_id = 123
        current_balance = 100.0
        required_balance = 200.0

        exception = InsufficientBalanceException(
            account_id=account_id,
            current_balance=current_balance,
            required_balance=required_balance
        )

        assert exception.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        expected_detail = (
            f"Insufficient balance in account {account_id}. "
            f"Current: {current_balance}, Required: {required_balance}"
        )
        assert exception.detail == expected_detail

    def test_insufficient_balance_with_zero_values(self):
        account_id = 123
        current_balance = 0.0
        required_balance = 50.0

        exception = InsufficientBalanceException(
            account_id=account_id,
            current_balance=current_balance,
            required_balance=required_balance
        )

        expected_detail = (
            f"Insufficient balance in account {account_id}. "
            f"Current: {current_balance}, Required: {required_balance}"
        )
        assert exception.detail == expected_detail


class TestDuplicateAccountException:

    def test_duplicate_account_exception(self):
        user_id = 789
        exception = DuplicateAccountException(user_id=user_id)

        assert exception.status_code == status.HTTP_409_CONFLICT
        assert exception.detail == f"Account for user {user_id} already exists"

    def test_duplicate_account_with_zero_user_id(self):
        user_id = 0
        exception = DuplicateAccountException(user_id=user_id)

        assert exception.detail == f"Account for user {user_id} already exists"


class TestInvalidAmountException:

    def test_invalid_amount_exception_positive(self):
        amount = 100.0
        exception = InvalidAmountException(amount=amount)

        assert exception.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert exception.detail == f"Invalid amount: {amount}. Amount must be positive"

    def test_invalid_amount_exception_negative(self):
        amount = -50.0
        exception = InvalidAmountException(amount=amount)

        assert exception.detail == f"Invalid amount: {amount}. Amount must be positive"

    def test_invalid_amount_exception_zero(self):
        amount = 0.0
        exception = InvalidAmountException(amount=amount)

        assert exception.detail == f"Invalid amount: {amount}. Amount must be positive"


class TestExceptionRaising:

    def test_account_not_found_exception_raising(self):
        with pytest.raises(AccountNotFoundException) as exc_info:
            raise AccountNotFoundException(account_id=999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Account with id 999 not found" in str(exc_info.value.detail)

    def test_insufficient_balance_exception_raising(self):
        with pytest.raises(InsufficientBalanceException) as exc_info:
            raise InsufficientBalanceException(
                account_id=111,
                current_balance=10.0,
                required_balance=100.0
            )

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "Insufficient balance" in str(exc_info.value.detail)

    def test_exception_chaining(self):
        exceptions_to_test = [
            (AccountNotFoundException(account_id=1), HTTPException),
            (InsufficientBalanceException(1, 10.0, 20.0), HTTPException),
            (DuplicateAccountException(1), HTTPException),
            (InvalidAmountException(-1), HTTPException),
        ]

        for exception, parent_class in exceptions_to_test:
            assert isinstance(exception, parent_class)


@pytest.mark.parametrize("account_id,user_id,expected_detail", [
    (None, None, "Account not found"),
    (1, None, "Account with id 1 not found"),
    (None, 2, "Account for user 2 not found"),
    (1, 2, "Account with id 1 not found"),
])
def test_account_not_found_parametrized(account_id, user_id, expected_detail):
    exception = AccountNotFoundException(account_id=account_id, user_id=user_id)
    assert exception.detail == expected_detail


@pytest.mark.parametrize("amount", [-100.0, -0.01, 0.0, 100.0])
def test_invalid_amount_parametrized(amount):
    exception = InvalidAmountException(amount=amount)
    assert f"Invalid amount: {amount}" in exception.detail
    assert "Amount must be positive" in exception.detail