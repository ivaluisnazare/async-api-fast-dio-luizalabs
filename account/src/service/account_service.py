from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
from typing import List

from account.src.models.account import accounts
from account.src.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
    DuplicateAccountException,
    InvalidAmountException
)


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_accounts(self, skip: int = 0, limit: int = 100) -> List[AccountResponse]:
        query = select(accounts).offset(skip).limit(limit)
        result = await self.db.execute(query)
        account_records = result.fetchall()
        return [AccountResponse.model_validate(account._asdict()) for account in account_records]

    async def get_account_by_id(self, account_id: int) -> AccountResponse:
        query = select(accounts).where(accounts.c.id == account_id)
        result = await self.db.execute(query)
        account_record = result.fetchone()

        if not account_record:
            raise AccountNotFoundException(account_id=account_id)

        return AccountResponse.model_validate(account_record._asdict())

    async def get_account_by_user_id(self, user_id: int) -> AccountResponse:
        query = select(accounts).where(accounts.c.user_id == user_id)
        result = await self.db.execute(query)
        account_record = result.fetchone()

        if not account_record:
            raise AccountNotFoundException(user_id=user_id)

        return AccountResponse.model_validate(account_record._asdict())

    async def create_account(self, account_data: AccountCreate) -> AccountResponse:
        existing_query = select(accounts).where(accounts.c.user_id == account_data.user_id)
        result = await self.db.execute(existing_query)
        if result.fetchone():
            raise DuplicateAccountException(account_data.user_id)

        query = accounts.insert().values(
            user_id=account_data.user_id,
            balance=account_data.balance
        ).returning(accounts)

        result = await self.db.execute(query)
        await self.db.commit()

        account_record = result.fetchone()
        return AccountResponse.model_validate(account_record._asdict())

    async def update_account(self, account_id: int, account_data: AccountUpdate) -> AccountResponse:
        await self.get_account_by_id(account_id)

        update_data = {}
        if account_data.balance is not None:
            update_data["balance"] = account_data.balance

        if update_data:
            query = (
                update(accounts)
                .where(accounts.c.id == account_id)
                .values(**update_data)
                .returning(accounts)
            )

            result = await self.db.execute(query)
            await self.db.commit()

            account_record = result.fetchone()
            return AccountResponse(**account_record._asdict())

        return await self.get_account_by_id(account_id)

    async def delete_account(self, account_id: int) -> bool:
        await self.get_account_by_id(account_id)

        query = accounts.delete().where(accounts.c.id == account_id)
        await self.db.execute(query)
        await self.db.commit()

        return True

    async def deposit(self, account_id: int, amount: Decimal) -> AccountResponse:
        if amount <= 0:
            raise InvalidAmountException(amount)

        query = (
            update(accounts)
            .where(accounts.c.id == account_id)
            .values(balance=accounts.c.balance + amount)
            .returning(accounts)
        )

        result = await self.db.execute(query)
        account_record = result.fetchone()

        if not account_record:
            raise AccountNotFoundException(account_id=account_id)

        await self.db.commit()
        return AccountResponse(**account_record._asdict())

    async def withdraw(self, account_id: int, amount: Decimal) -> AccountResponse:
        if amount <= 0:
            raise InvalidAmountException(amount)

        current_account = await self.get_account_by_id(account_id)
        if current_account.balance < amount:
            raise InsufficientBalanceException(
                account_id=account_id,
                current_balance=current_account.balance,
                required_balance=amount
            )

        query = (
            update(accounts)
            .where(accounts.c.id == account_id)
            .values(balance=accounts.c.balance - amount)
            .returning(accounts)
        )

        result = await self.db.execute(query)
        account_record = result.fetchone()

        await self.db.commit()
        return AccountResponse(**account_record._asdict())

    async def transfer(self, from_account_id: int, to_account_id: int, amount: Decimal) -> dict:
        if amount <= 0:
            raise InvalidAmountException(amount)

        await self.get_account_by_id(from_account_id)
        await self.get_account_by_id(to_account_id)

        try:
            from_account = await self.withdraw(from_account_id, amount)
            to_account = await self.deposit(to_account_id, amount)

            return {
                "from_account": from_account,
                "to_account": to_account,
                "amount": amount,
                "message": "Transfer completed successfully"
            }
        except Exception as e:
            await self.db.rollback()
            raise e