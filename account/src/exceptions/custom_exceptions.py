#custom_exceptions.py
from fastapi import HTTPException, status

class AccountException(HTTPException):
    """Base exception for account-related errors"""
    pass

class AccountNotFoundException(AccountException):
    def __init__(self, account_id: int = None, user_id: int = None):
        if account_id is not None:
            detail = f"Account with id {account_id} not found"
        elif user_id is not None:
            detail = f"Account for user {user_id} not found"
        else:
            detail = "Account not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class InsufficientBalanceException(AccountException):
    def __init__(self, account_id: int, current_balance: float, required_balance: float):
        detail = (
            f"Insufficient balance in account {account_id}. "
            f"Current: {current_balance}, Required: {required_balance}"
        )
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)

class DuplicateAccountException(AccountException):
    def __init__(self, user_id: int):
        detail = f"Account for user {user_id} already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class InvalidAmountException(AccountException):
    def __init__(self, amount: float):
        detail = f"Invalid amount: {amount}. Amount must be positive"
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)