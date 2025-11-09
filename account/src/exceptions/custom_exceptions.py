from fastapi import HTTPException, status


class AccountException(HTTPException):
    pass


class AccountNotFoundException(AccountException):
    def __init__(self, account_id: int = None, user_id: int = None):
        detail = "Account not found"
        if account_id:
            detail = f"Account with id {account_id} not found"
        elif user_id:
            detail = f"Account for user {user_id} not found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class InsufficientBalanceException(AccountException):
    def __init__(self, account_id: int, current_balance: float, required_balance: float):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Insufficient balance in account {account_id}. "
                   f"Current: {current_balance}, Required: {required_balance}"
        )


class DuplicateAccountException(AccountException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account for user {user_id} already exists"
        )


class InvalidAmountException(AccountException):
    def __init__(self, amount: float):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid amount: {amount}. Amount must be positive"
        )