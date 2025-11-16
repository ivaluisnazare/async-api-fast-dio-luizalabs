from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List

from account.src.repository.account_repository import AccountRepository
from account.src.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
    InvalidAmountException
)


class AccountService:
    def __init__(self, db: AsyncSession):
        self.repository = AccountRepository(db)
        self.db = db

    async def get_all_accounts(self, skip: int = 0, limit: int = 100) -> List[AccountResponse]:
        account_records = await self.repository.get_all(skip, limit)
        return [AccountResponse.model_validate(account) for account in account_records]

    async def get_account_by_id(self, account_id: int) -> AccountResponse:
        account_record = await self.repository.get_by_id(account_id)
        if not account_record:
            raise AccountNotFoundException(account_id=account_id)
        return AccountResponse.model_validate(account_record)

    async def get_account_by_user_id(self, user_id: int) -> AccountResponse:
        account_record = await self.repository.get_by_user_id(user_id)
        if not account_record:
            raise AccountNotFoundException(user_id=user_id)
        return AccountResponse.model_validate(account_record)

    async def create_account(self, account_data: AccountCreate) -> AccountResponse:
        try:
            account_record = await self.repository.create(account_data)
            await self.db.commit()
            return AccountResponse.model_validate(account_record)
        except Exception:
            await self.db.rollback()
            raise

    async def update_account(self, account_id: int, account_data: AccountUpdate) -> AccountResponse:
        try:
            # Verificar se a conta existe
            await self.get_account_by_id(account_id)

            account_record = await self.repository.update(account_id, account_data)
            await self.db.commit()
            return AccountResponse.model_validate(account_record)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_account(self, account_id: int) -> bool:
        try:
            # Verificar se a conta existe
            await self.get_account_by_id(account_id)

            result = await self.repository.delete(account_id)
            await self.db.commit()
            return result
        except Exception:
            await self.db.rollback()
            raise

    async def deposit(self, account_id: int, amount: Decimal) -> AccountResponse:
        if amount <= 0:
            raise InvalidAmountException(amount)

        try:
            current_balance = await self.repository.get_balance(account_id)
            new_balance = current_balance + amount

            account_record = await self.repository.update_balance(account_id, new_balance)
            await self.db.commit()
            return AccountResponse.model_validate(account_record)
        except Exception:
            await self.db.rollback()
            raise

    async def withdraw(self, account_id: int, amount: Decimal) -> AccountResponse:
        if amount <= 0:
            raise InvalidAmountException(amount)

        try:
            current_balance = await self.repository.get_balance(account_id)

            if current_balance < amount:
                raise InsufficientBalanceException(
                    account_id=account_id,
                    current_balance=current_balance,
                    required_balance=amount
                )

            new_balance = current_balance - amount
            account_record = await self.repository.update_balance(account_id, new_balance)
            await self.db.commit()
            return AccountResponse.model_validate(account_record)
        except Exception:
            await self.db.rollback()
            raise

    async def transfer(self, from_account_id: int, to_account_id: int, amount: Decimal) -> dict:
        if amount <= 0:
            raise InvalidAmountException(amount)

        try:
            # Usar transação explícita
            async with self.db.begin():
                # Verificar se as contas existem e obter saldos
                from_balance = await self.repository.get_balance(from_account_id)
                to_balance = await self.repository.get_balance(to_account_id)

                # Verificar saldo suficiente
                if from_balance < amount:
                    raise InsufficientBalanceException(
                        account_id=from_account_id,
                        current_balance=from_balance,
                        required_balance=amount
                    )

                # Atualizar saldos
                from_new_balance = from_balance - amount
                to_new_balance = to_balance + amount

                from_account_record = await self.repository.update_balance(from_account_id, from_new_balance)
                to_account_record = await self.repository.update_balance(to_account_id, to_new_balance)

                return {
                    "from_account": AccountResponse.model_validate(from_account_record),
                    "to_account": AccountResponse.model_validate(to_account_record),
                    "amount": amount,
                    "message": "Transfer completed successfully"
                }
        except Exception as e:
            await self.db.rollback()
            raise e